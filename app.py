import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import warnings

warnings.filterwarnings('ignore')

# Page Configuration for an elegant aesthetic
st.set_page_config(
    page_title="SecureCheck Police DB System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("<h1 class='gradient-text'> SecureCheck: Police Post Ledger</h1>", unsafe_allow_html=True)
st.caption("A Centralized Python-SQL Database System for Real-Time Law Enforcement Stop Logging & Analysis")

# Database Connection Helper
DB_PATH = 'database.db'

def run_query(query: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"SQL Error: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# Initialize Tabs
tab_live, tab_analytics, tab_queries = st.tabs([
    "Live Logs & Filters",
    "Advanced Analytics",
    "Pre-defined SQL Reports"
])

with tab_live:
    st.subheader("Live Check Post Operations")

    # Quick Stats Row
    with st.container():
        cols = st.columns(4)
        total_stops = run_query("SELECT COUNT(*) AS c FROM traffic_stops").iloc[0]['c']
        total_arrests = run_query("SELECT COUNT(*) AS c FROM traffic_stops WHERE is_arrested=1").iloc[0]['c']
        total_searches = run_query("SELECT COUNT(*) AS c FROM traffic_stops WHERE search_conducted=1").iloc[0]['c']
        drug_stops = run_query("SELECT COUNT(*) AS c FROM traffic_stops WHERE drugs_related_stop=1").iloc[0]['c']
        
        cols[0].metric(label="Total Vehicles Stopped", value=f"{total_stops:,}")
        cols[1].metric(label="Total Arrests Made", value=f"{total_arrests:,}")
        cols[2].metric(label="Searches Conducted", value=f"{total_searches:,}")
        cols[3].metric(label="Drug Related Incidents", value=f"{drug_stops:,}")
        
    st.divider()

    st.markdown("### Intelligent Log Lookup")
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        v_num = st.text_input("Vehicle Number (Exact or Partial)", "")
    with f_col2:
        reason = st.selectbox("Reason for Stop", ["All"] + list(run_query("SELECT DISTINCT violation FROM traffic_stops WHERE violation != '0'")['violation']))
    with f_col3:
        arrest_only = st.checkbox("Show Only Resulted in Arrest", value=False)
        
    query = "SELECT stop_date, stop_time, vehicle_number, driver_age, driver_gender, violation, stop_outcome, is_arrested FROM traffic_stops WHERE 1=1 "
    if v_num:
        query += f" AND vehicle_number LIKE '%{v_num}%' "
    if reason != "All":
        query += f" AND violation = '{reason}' "
    if arrest_only:
        query += " AND is_arrested = 1 "
    query += " ORDER BY stop_date DESC LIMIT 500"
    
    logs_df = run_query(query)
    
    # Custom display format
    st.dataframe(logs_df, use_container_width=True, hide_index=True)


with tab_analytics:
    st.subheader("Data-Backed Decision Analytics")
    
    row1_c1, row1_c2 = st.columns(2)
    
    with row1_c1:
        st.markdown("**Stops by Time of Day**")
        df_time = run_query('''
        SELECT substr(stop_time, 1, instr(stop_time, ':') - 1) as hour, COUNT(*) as stops 
        FROM traffic_stops 
        WHERE stop_time != '0' 
        GROUP BY hour 
        ORDER BY cast(hour as integer)
        ''')
        fig1 = px.line(df_time, x='hour', y='stops', markers=True, template='plotly_dark', line_shape='spline',
                       color_discrete_sequence=['#58a6ff'])
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)

    with row1_c2:
        st.markdown("**Stops by Country**")
        df_country = run_query("SELECT country_name, COUNT(*) as total FROM traffic_stops WHERE country_name != '0' GROUP BY country_name ORDER BY total DESC")
        fig2 = px.bar(df_country, x='country_name', y='total', template='plotly_dark', color='total', color_continuous_scale='Blues')
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)


with tab_queries:
    st.subheader("Requested SQL Evaluation Queries")
    
    queries = {
        "1. Top 10 vehicles in drug-related stops": "SELECT vehicle_number, COUNT(*) as incidents FROM traffic_stops WHERE drugs_related_stop=1 AND vehicle_number != '0' GROUP BY vehicle_number ORDER BY incidents DESC LIMIT 10;",
        "2. Which vehicles were most frequently searched?": "SELECT vehicle_number, COUNT(*) as search_count FROM traffic_stops WHERE search_conducted=1 AND vehicle_number != '0' GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10;",
        "4. Driver age group with highest arrest rate": """
            SELECT 
                CASE 
                    WHEN driver_age < 21 THEN 'Under 21'
                    WHEN driver_age BETWEEN 21 AND 30 THEN '21-30'
                    WHEN driver_age BETWEEN 31 AND 40 THEN '31-40'
                    WHEN driver_age BETWEEN 41 AND 50 THEN '41-50'
                    ELSE 'Over 50' END AS age_group,
                ROUND(AVG(is_arrested)*100, 2) as arrest_rate_percentage
            FROM traffic_stops
            WHERE driver_age != 0
            GROUP BY age_group ORDER BY arrest_rate_percentage DESC;
        """,
        "5. Gender distribution in each country": "SELECT country_name, driver_gender, COUNT(*) as total FROM traffic_stops WHERE country_name != '0' AND driver_gender != '0' GROUP BY country_name, driver_gender;",
        "6. Race and gender combination with highest search rate": """
            SELECT driver_race, driver_gender, ROUND(AVG(search_conducted)*100, 2) as search_rate_pct 
            FROM traffic_stops WHERE driver_race != '0' AND driver_gender != '0' GROUP BY driver_race, driver_gender ORDER BY search_rate_pct DESC LIMIT 5;
        """,
        "7. What time of day sees the most traffic stops?": """
            SELECT substr(stop_time, 1, instr(stop_time, ':') - 1) as hour_of_day, COUNT(*) as total_stops 
            FROM traffic_stops WHERE stop_time != '0' GROUP BY hour_of_day ORDER BY total_stops DESC LIMIT 5;
        """,
        "8. Average stop duration for different violations": """
            SELECT violation, stop_duration, COUNT(*) as count 
            FROM traffic_stops WHERE stop_duration != '0' GROUP BY violation, stop_duration ORDER BY violation, count DESC;
        """,
        "10. Which violations are most associated with searches or arrests?": """
            SELECT violation, ROUND(AVG(search_conducted)*100, 2) as search_rate, ROUND(AVG(is_arrested)*100, 2) as arrest_rate 
            FROM traffic_stops GROUP BY violation ORDER BY arrest_rate DESC;
        """,
        "13. Countries reporting highest rate of drug-related stops": """
            SELECT country_name, ROUND(AVG(drugs_related_stop)*100, 2) as drug_stop_rate 
            FROM traffic_stops WHERE country_name != '0' GROUP BY country_name ORDER BY drug_stop_rate DESC;
        """,
        "Complex 1: Top 5 Violations with Highest Arrest Rates": """
            SELECT violation, COUNT(*) as total_stops, SUM(is_arrested) as arrests, ROUND(AVG(is_arrested)*100,2) as arrest_rate
            FROM traffic_stops GROUP BY violation HAVING total_stops > 100 ORDER BY arrest_rate DESC LIMIT 5;
        """
    }
    
    q_choice = st.selectbox("Select Answer to View", list(queries.keys()))
    
    st.code(queries[q_choice], language="sql")
    
    res_df = run_query(queries[q_choice])
    st.dataframe(res_df, use_container_width=True)

