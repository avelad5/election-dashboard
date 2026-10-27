import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="Election Prediction Game", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🗳️ Election Day Prediction Dashboard</h1>", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    # קריאת קובץ האקסל
    df = pd.read_excel("the groups votes.xlsx")
    
    # זיהוי עמודות המפלגות (הכל מלבד חותמת זמן ושם)
    party_cols = [col for col in df.columns if col not in ['חותמת זמן', 'name']]
    
    # חישוב סך המנדטים שניחש כל אחד
    df['Total Seats'] = df[party_cols].sum(axis=1)
    
    return df, party_cols

df, party_cols = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📊 Group Overview", "🔍 Deep Dive Insights", "👤 Individual Guesses", "🏆 Live Results & Leaderboard"])

# --- Page 1: Group Overview ---
if page == "📊 Group Overview":
    st.subheader("The Group's Predictions")
    
    # הכנת הטבלה לתצוגה ללא עמודת חותמת הזמן
    display_df = df.drop(columns=['חותמת זמן'])
    
    # פונקציה לצביעת 3 המפלגות הגדולות בכל שורה (לכל משתתף בנפרד)
    def highlight_top_3(row):
        # דירוג הערכים בשורה (1 למספר הגדול ביותר, 2 לשני וכו')
        ranks = row.rank(method='dense', ascending=False)
        styles = []
        for r in ranks:
            if r == 1:
                styles.append('background-color: #1E3A8A; color: white;') # כחול כהה למקום ה-1
            elif r == 2:
                styles.append('background-color: #3B82F6; color: white;') # כחול רגיל למקום ה-2
            elif r == 3:
                styles.append('background-color: #93C5FD; color: black;') # תכלת למקום ה-3
            else:
                styles.append('') # ללא צבע לשאר
        return styles
    
    # החלת העיצוב: הפעלת הפונקציה שורתית (axis=1), מרכוז טקסט ופונט
    styled_df = display_df.style.apply(
        highlight_top_3, axis=1, subset=party_cols
    ).format(precision=0).set_properties(**{'text-align': 'center', 'font-size': '15px'})
    
    # הצגת הטבלה המעוצבת לרוחב מלא ללא עמודת האינדקס
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- Page 2: Deep Dive Insights ---
elif page == "🔍 Deep Dive Insights":
    st.subheader("Interesting Segmentations")
    
    # חישוב סטטיסטיקות לכל מפלגה
    stats = []
    for party in party_cols:
        stats.append({
            'Party': party,
            'Average Guess': df[party].mean(),
            'Max Guess (Optimistic)': df[party].max(),
            'Min Guess (Pessimistic)': df[party].min()
        })
    stats_df = pd.DataFrame(stats).sort_values(by='Average Guess', ascending=False)
    
    st.markdown("**Average Mandates per Party**")
    fig_avg = px.bar(stats_df, x='Party', y='Average Guess', text_auto='.1f', color='Party')
    st.plotly_chart(fig_avg, use_container_width=True)

# --- Page 3: Individual Views ---
elif page == "👤 Individual Guesses":
    st.subheader("Explore a Friend's Prediction")
    person = st.selectbox("Select a friend:", df['name'].unique())
    
    # שליפת הנתונים עבור החבר שנבחר
    person_data = df[df['name'] == person][party_cols].T.reset_index()
    person_data.columns = ['Party', 'Mandates']
    person_data = person_data[person_data['Mandates'] > 0] # סינון 0 לתצוגה נקייה יותר
    
    # יצירת גרף עוגה
    fig_pie = px.pie(person_data, values='Mandates', names='Party', title=f"{person}'s Knesset Composition", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Page 4: Live Results & Leaderboard ---
elif page == "🏆 Live Results & Leaderboard":
    st.subheader("Enter Exit Polls or Final Results")
    st.write("Enter the actual mandates below. The system will calculate who is the closest!")
    
    # יצירת טבלה התחלתית לתוצאות האמת
    if 'actual_results' not in st.session_state:
        default_actuals = pd.DataFrame([{"Party": p, "Actual Mandates": 0} for p in party_cols])
        st.session_state.actual_results = default_actuals
        
    # רכיב עריכת נתונים להזנה חיה
    edited_actuals = st.data_editor(st.session_state.actual_results, use_container_width=True, hide_index=True)
    
    if st.button("Calculate Winner"):
        actual_dict = dict(zip(edited_actuals['Party'], edited_actuals['Actual Mandates']))
        
        scores = []
        for idx, row in df.iterrows():
            error = 0
            for p in party_cols:
                # חישוב הפער המוחלט בין הניחוש לתוצאה
                error += abs(row[p] - actual_dict[p])
            scores.append({'Name': row['name'], 'Total Error (Lower is better)': error})
            
        # מיון הטבלה מהפער הקטן לגדול
        leaderboard = pd.DataFrame(scores).sort_values(by='Total Error (Lower is better)')
        st.balloons()
        st.markdown("### 🏆 Leaderboard")
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)