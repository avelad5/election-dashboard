import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="Election Prediction Game", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🗳️ Election Day Prediction Dashboard</h1>", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    # קריאת קובץ הניחושים
    df = pd.read_excel("the groups votes.xlsx")
    party_cols = [col for col in df.columns if col not in ['חותמת זמן', 'name']]
    df['Total Seats'] = df[party_cols].sum(axis=1)
    return df, party_cols

df, party_cols = load_data()

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["📊 Group Overview", "🔍 Deep Dive Insights", "👤 Individual Guesses", "🏆 Live Results & Leaderboard"])

# --- Page 1: Group Overview ---
if page == "📊 Group Overview":
    st.subheader("The Group's Predictions")
    display_df = df.drop(columns=['חותמת זמן'])
    
    def highlight_top_3(row):
        ranks = row.rank(method='dense', ascending=False)
        styles = []
        for r in ranks:
            if r == 1:
                styles.append('background-color: #1E3A8A; color: white;')
            elif r == 2:
                styles.append('background-color: #3B82F6; color: white;')
            elif r == 3:
                styles.append('background-color: #93C5FD; color: black;')
            else:
                styles.append('')
        return styles
    
    styled_df = display_df.style.apply(
        highlight_top_3, axis=1, subset=party_cols
    ).format(precision=0).set_properties(**{'text-align': 'center', 'font-size': '15px'})
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

# --- Page 2: Deep Dive Insights ---
elif page == "🔍 Deep Dive Insights":
    st.subheader("Interesting Segmentations")
    
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
    
    person_data = df[df['name'] == person][party_cols].T.reset_index()
    person_data.columns = ['Party', 'Mandates']
    person_data = person_data[person_data['Mandates'] > 0]
    
    fig_pie = px.pie(person_data, values='Mandates', names='Party', title=f"{person}'s Knesset Composition", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Page 4: Live Results & Leaderboard ---
elif page == "🏆 Live Results & Leaderboard":
    st.subheader("Live Results & Leaderboard")
    
    try:
        # טעינת נתוני האמת
        real_df = pd.read_excel("real votes.xlsx")
        
        # לוקחים רק את העמודות של המפלגות מהשורה הראשונה בקובץ
        real_results = real_df[party_cols].iloc[0]
        
        st.markdown("### 📊 Actual Election Results (תוצאות האמת)")
        
        # הפיכה ל-DataFrame לעיצוב והצגה
        display_real_df = pd.DataFrame([real_results])
        
        # עיצוב מודרני מודגש לירוק
        styled_real = display_real_df.style.background_gradient(
            cmap='Greens', axis=1
        ).format(precision=0).set_properties(**{
            'text-align': 'center', 
            'font-size': '16px', 
            'font-weight': 'bold',
            'border': '1px solid #10B981'
        })
        
        st.dataframe(styled_real, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.write("Click below to calculate everyone's penalty score. Every 1 mandate difference equals 1 penalty point. **The lowest score wins!**")
        
        if st.button("🏆 Calculate Winner"):
            scores = []
            # חישוב הנקודות הרעות לכל משתתף
            for idx, row in df.iterrows():
                error = 0
                for p in party_cols:
                    # הסטייה היא הערך המוחלט בין הניחוש לבין תוצאת האמת
                    error += abs(row[p] - real_results[p])
                scores.append({'Name': row['name'], 'Total Penalty Points': error})
                
            # סידור הטבלה מהציון הנמוך (המנצח) לגבוה
            leaderboard = pd.DataFrame(scores).sort_values(by='Total Penalty Points').reset_index(drop=True)
            
            st.balloons()
            st.markdown("### 🏆 Final Leaderboard")
            
            # פונקציה לצביעת השורה של המנצח (המקום הראשון)
            def highlight_winner(row):
                if row.name == 0:
                    return ['background-color: #FFD700; color: black; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            styled_leaderboard = leaderboard.style.apply(highlight_winner, axis=1).set_properties(**{'text-align': 'center', 'font-size': '15px'})
            st.dataframe(styled_leaderboard, use_container_width=True, hide_index=True)
            
            # הודעת ניצחון
            winner_name = leaderboard.iloc[0]['Name']
            winning_score = leaderboard.iloc[0]['Total Penalty Points']
            st.success(f"🎉 **{winner_name}** is the winner with the lowest penalty score of {winning_score} points!")

    except FileNotFoundError:
        st.warning("The file 'real votes.xlsx' was not found. Please ensure it is in the same folder.")
    except Exception as e:
        st.error(f"An error occurred: {e}")