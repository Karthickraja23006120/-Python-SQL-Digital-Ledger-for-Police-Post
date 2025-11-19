# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# -----------------------
# Config & Constants
# -----------------------
DATABASE_FILE = "securecheck_police_logs.db"
TABLE_NAME = "police_stop_logs"

st.set_page_config(layout="wide", page_title="SecureCheck Digital Ledger")

# -----------------------
# Database helpers
# -----------------------
def get_db_connection():
    """Return a new sqlite3 connection (no caching)."""
    conn = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create table if not exists with a proper primary key (stop_id)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            stop_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stop_datetime TEXT,
            country_name TEXT,
            vehicle_number TEXT,
            driver_gender TEXT,
            driver_age INTEGER,
            driver_race TEXT,
            violation TEXT,
            stop_duration TEXT,
            stop_outcome TEXT,
            search_conducted INTEGER,
            search_type TEXT,
            is_arrested INTEGER,
            drugs_related_stop INTEGER
        );
    """)
    conn.commit()
    conn.close()

def run_query(sql, params=None):
    conn = get_db_connection()
    try:
        if params:
            df = pd.read_sql_query(sql, conn, params=params)
        else:
            df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df

def insert_log(values_tuple):
    conn = get_db_connection()
    try:
        insert_sql = f"""
            INSERT INTO {TABLE_NAME}
            (stop_datetime, country_name, vehicle_number,
             driver_gender, driver_age, driver_race, violation,
             stop_duration, stop_outcome, search_conducted,
             search_type, is_arrested, drugs_related_stop)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);
        """
        cur = conn.cursor()
        cur.execute(insert_sql, values_tuple)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_table_info():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({TABLE_NAME});")
        return cur.fetchall()
    finally:
        conn.close()

# -----------------------
# SQL_QUERIES (Medium + Complex)
# -----------------------
SQL_QUERIES = {
    # Vehicle-Based
    "Top 10 vehicles in drug-related stops": """
        SELECT vehicle_number, COUNT(*) AS drug_stop_count
        FROM police_stop_logs
        WHERE drugs_related_stop = 1
        GROUP BY vehicle_number
        ORDER BY drug_stop_count DESC
        LIMIT 10;
    """,
    "Most frequently searched vehicles (Top 20)": """
        SELECT vehicle_number, COUNT(*) AS search_count
        FROM police_stop_logs
        WHERE search_conducted = 1
        GROUP BY vehicle_number
        ORDER BY search_count DESC
        LIMIT 20;
    """,

    # Demographic-Based
    "Driver age group with highest arrest rate": """
        WITH age_buckets AS (
          SELECT
            CASE
              WHEN driver_age < 18 THEN '<18'
              WHEN driver_age BETWEEN 18 AND 24 THEN '18-24'
              WHEN driver_age BETWEEN 25 AND 34 THEN '25-34'
              WHEN driver_age BETWEEN 35 AND 44 THEN '35-44'
              WHEN driver_age BETWEEN 45 AND 54 THEN '45-54'
              WHEN driver_age >= 55 THEN '55+'
              ELSE 'Unknown'
            END AS age_group,
            is_arrested
          FROM police_stop_logs
        )
        SELECT age_group,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM age_buckets
        GROUP BY age_group
        ORDER BY arrest_rate_pct DESC;
    """,
    "Gender distribution by country": """
        SELECT country_name, driver_gender, COUNT(*) AS stops
        FROM police_stop_logs
        GROUP BY country_name, driver_gender
        ORDER BY country_name, stops DESC;
    """,
    "Race+Gender combination with highest search rate": """
        SELECT driver_race, driver_gender, COUNT(*) AS total_stops,
               SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
               CAST(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS search_rate_pct
        FROM police_stop_logs
        GROUP BY driver_race, driver_gender
        HAVING COUNT(*) >= 20
        ORDER BY search_rate_pct DESC
        LIMIT 10;
    """,

    # Time & Duration
    "Stops by hour of day": """
        SELECT CAST(strftime('%H', stop_datetime) AS INTEGER) AS hour_of_day, COUNT(*) AS stops
        FROM police_stop_logs
        WHERE stop_datetime IS NOT NULL
        GROUP BY hour_of_day
        ORDER BY stops DESC;
    """,
    "Average stop duration for each violation (minutes)": """
        WITH mapped AS (
          SELECT violation,
                 CASE stop_duration
                   WHEN '0-15 Min' THEN 7.5
                   WHEN '16-30 Min' THEN 23.0
                   WHEN '>30 Min' THEN 45.0
                   ELSE NULL
                 END AS duration_minutes
          FROM police_stop_logs
        )
        SELECT violation, COUNT(duration_minutes) AS n_samples, AVG(duration_minutes) AS avg_duration_minutes
        FROM mapped
        GROUP BY violation
        ORDER BY avg_duration_minutes DESC;
    """,
    "Are night stops more likely to lead to arrests?": """
        WITH flagged AS (
          SELECT *, CAST(strftime('%H', stop_datetime) AS INTEGER) AS hour
          FROM police_stop_logs
        )
        SELECT CASE WHEN hour >= 20 OR hour <= 4 THEN 'night' ELSE 'day' END AS period,
               COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM flagged
        GROUP BY period
        ORDER BY arrest_rate_pct DESC;
    """,

    # Violation-Based
    "Violations most associated with searches or arrests": """
        SELECT violation, COUNT(*) AS total_stops,
               SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS search_rate_pct,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM police_stop_logs
        GROUP BY violation
        HAVING COUNT(*) > 10
        ORDER BY arrest_rate_pct DESC, search_rate_pct DESC;
    """,
    "Violations common among drivers <25": """
        SELECT violation,
               COUNT(*) AS stops_under25,
               CAST(COUNT(*) AS REAL) / (SELECT COUNT(*) FROM police_stop_logs WHERE driver_age < 25) * 100.0 AS pct_of_under25_stops
        FROM police_stop_logs
        WHERE driver_age < 25
        GROUP BY violation
        ORDER BY stops_under25 DESC
        LIMIT 20;
    """,
    "Violations that rarely result in search or arrest": """
        SELECT violation, COUNT(*) AS total_stops,
               CAST(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS search_rate_pct,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM police_stop_logs
        GROUP BY violation
        HAVING COUNT(*) > 50
        ORDER BY (search_rate_pct + arrest_rate_pct) ASC
        LIMIT 10;
    """,

    # Location-Based
    "Countries with highest drug-related stop rate": """
        SELECT country_name, COUNT(*) AS total_stops,
               SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS drug_stops,
               CAST(SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS drug_rate_pct
        FROM police_stop_logs
        GROUP BY country_name
        HAVING COUNT(*) > 50
        ORDER BY drug_rate_pct DESC
        LIMIT 10;
    """,
    "Arrest rate by country and violation": """
        SELECT country_name, violation, COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM police_stop_logs
        GROUP BY country_name, violation
        HAVING COUNT(*) >= 10
        ORDER BY arrest_rate_pct DESC
        LIMIT 50;
    """,
    "Country with most searches conducted": """
        SELECT country_name,
               SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
               COUNT(*) AS total_stops,
               CAST(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS search_rate_pct
        FROM police_stop_logs
        GROUP BY country_name
        ORDER BY searches DESC
        LIMIT 10;
    """,

    # Complex Queries
    "Yearly breakdown of stops and arrests by country": """
        WITH parsed AS (
          SELECT country_name, CAST(strftime('%Y', stop_datetime) AS INTEGER) AS year, is_arrested
          FROM police_stop_logs
        )
        SELECT country_name, year,
               COUNT(*) AS stops,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct,
               SUM(COUNT(*)) OVER (PARTITION BY country_name ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_stops
        FROM parsed
        GROUP BY country_name, year
        ORDER BY country_name, year;
    """,
    "Driver violation trends by age & race": """
        WITH age_grouped AS (
          SELECT *,
            CASE
              WHEN driver_age < 18 THEN '<18'
              WHEN driver_age BETWEEN 18 AND 24 THEN '18-24'
              WHEN driver_age BETWEEN 25 AND 34 THEN '25-34'
              WHEN driver_age BETWEEN 35 AND 44 THEN '35-44'
              WHEN driver_age BETWEEN 45 AND 54 THEN '45-54'
              WHEN driver_age >= 55 THEN '55+'
              ELSE 'Unknown' END AS age_group
          FROM police_stop_logs
        )
        SELECT age_group, driver_race, violation,
               COUNT(*) AS stops,
               CAST(COUNT(*) AS REAL) * 100.0 / (SELECT COUNT(*) FROM police_stop_logs WHERE driver_age IS NOT NULL AND driver_age >= 0) AS pct_of_all_stops
        FROM age_grouped
        GROUP BY age_group, driver_race, violation
        ORDER BY age_group, stops DESC
        LIMIT 200;
    """,
    "Stops by year, month, hour": """
        SELECT CAST(strftime('%Y', stop_datetime) AS INTEGER) AS year,
               CAST(strftime('%m', stop_datetime) AS INTEGER) AS month,
               CAST(strftime('%H', stop_datetime) AS INTEGER) AS hour,
               COUNT(*) AS stops
        FROM police_stop_logs
        GROUP BY year, month, hour
        ORDER BY year DESC, month DESC, hour;
    """,
    "Violations with high search & arrest rates (ranked)": """
        WITH stats AS (
          SELECT violation, COUNT(*) AS total,
                 SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
                 SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
                 CAST(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS search_rate_pct,
                 CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
          FROM police_stop_logs
          GROUP BY violation
          HAVING COUNT(*) > 30
        )
        SELECT *, RANK() OVER (ORDER BY arrest_rate_pct DESC) AS rank_by_arrest_rate,
                  RANK() OVER (ORDER BY search_rate_pct DESC) AS rank_by_search_rate
        FROM stats
        ORDER BY rank_by_arrest_rate, rank_by_search_rate
        LIMIT 30;
    """,
    "Driver demographics by country": """
        SELECT country_name, driver_gender,
               CASE
                 WHEN driver_age < 18 THEN '<18'
                 WHEN driver_age BETWEEN 18 AND 24 THEN '18-24'
                 WHEN driver_age BETWEEN 25 AND 34 THEN '25-34'
                 WHEN driver_age BETWEEN 35 AND 44 THEN '35-44'
                 WHEN driver_age BETWEEN 45 AND 54 THEN '45-54'
                 WHEN driver_age >= 55 THEN '55+'
                 ELSE 'Unknown'
               END AS age_group,
               driver_race,
               COUNT(*) AS stops
        FROM police_stop_logs
        GROUP BY country_name, driver_gender, age_group, driver_race
        ORDER BY country_name, stops DESC
        LIMIT 500;
    """,
    "Top 5 violations with highest arrest rates": """
        SELECT violation, COUNT(*) AS total_stops,
               SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
               CAST(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS REAL) * 100.0 / COUNT(*) AS arrest_rate_pct
        FROM police_stop_logs
        GROUP BY violation
        HAVING COUNT(*) >= 30
        ORDER BY arrest_rate_pct DESC
        LIMIT 5;
    """,
}

# -----------------------
# UI: Login / Role (demo)
# -----------------------
if "role" not in st.session_state:
    st.session_state.role = None

with st.sidebar:
    st.header("User")
    if st.session_state.role is None:
        role = st.selectbox("Select role (demo)", ["Officer", "Admin"])
        if st.button("Login"):
            st.session_state.role = role
            st.success(f"Logged in as {role}")
    else:
        st.write(f"Logged in as: **{st.session_state.role}**")
        if st.button("Logout"):
            st.session_state.role = None
            st.experimental_rerun()

# -----------------------
# Initialize DB
# -----------------------
init_db()

# -----------------------
# Top-level header & quick KPIs
# -----------------------
st.title("🚓 SecureCheck: Police Post Digital Ledger")
st.markdown("Real-time logs, analytics, and automated alerts for check posts.")

# KPI Row
def load_kpis():
    sql = f"""
        SELECT
          COUNT(*) AS total_stops,
          SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
          SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS total_drug_stops
        FROM {TABLE_NAME};
    """
    return run_query(sql).iloc[0]

kpis = load_kpis()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stops", int(kpis["total_stops"]))
col2.metric("Total Arrests", int(kpis["total_arrests"]))
drug_rate = (int(kpis["total_drug_stops"]) / int(kpis["total_stops"]) * 100.0) if kpis["total_stops"] > 0 else 0.0
col3.metric("Drug-related %", f"{drug_rate:.1f}%")
col4.metric("Unique Vehicles", run_query(f"SELECT COUNT(DISTINCT vehicle_number) AS uv FROM {TABLE_NAME};").iloc[0]["uv"])

st.markdown("---")

# -----------------------
# Section 1: Real-time Logging Form
# -----------------------
st.header("📝 Add New Police Log & Check Vehicle Status")

with st.form("new_log_form"):
    st.subheader("Stop Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        stop_date = st.date_input("Stop Date", datetime.today().date())
        stop_time = st.time_input("Stop Time", datetime.now().time())
        country_name = st.text_input("Country Name", "India")
        vehicle_number = st.text_input("Vehicle Number", placeholder="RJ01AB1234").upper().strip()
    with col2:
        driver_gender = st.selectbox("Driver Gender", ['M', 'F', 'Unknown'])
        driver_age = st.number_input("Driver Age", min_value=0, max_value=120, value=30)
        driver_race = st.text_input("Driver Race", "Other")
        violation = st.selectbox("Violation", ['Speeding', 'DUI', 'Signal', 'Seatbelt', 'Equipment', 'Other'])
    with col3:
        stop_duration = st.selectbox("Stop Duration", ['0-15 Min', '16-30 Min', '>30 Min'])
        search_conducted = st.selectbox("Was a Search Conducted?", [0, 1], format_func=lambda x: 'Yes' if x == 1 else 'No')
        search_type = st.text_input("Search Type (if applicable)", "No Search" if search_conducted == 0 else "Frisk")
        stop_outcome = st.selectbox("Stop Outcome", ['Warning', 'Citation', 'Arrest'])
        is_arrested = st.selectbox("Was Arrested?", [0, 1], format_func=lambda x: 'Yes' if x == 1 else 'No')
        drugs_related_stop = st.selectbox("Was Drug Related?", [0, 1], format_func=lambda x: 'Yes' if x == 1 else 'No')

    st.markdown("---")
    submitted = st.form_submit_button("Log Stop and Check Vehicle")

    if submitted:
        # Basic validation
        if not vehicle_number or len(vehicle_number) < 4:
            st.error("Provide a valid vehicle number.")
        else:
            stop_datetime = datetime.combine(stop_date, stop_time).strftime('%Y-%m-%d %H:%M:%S')
            # real-time flagging
            flag_query = f"SELECT COUNT(*) AS c FROM {TABLE_NAME} WHERE vehicle_number = ? AND is_arrested = 1;"
            arrest_count = run_query(flag_query, params=[vehicle_number]).iloc[0]["c"]
            if arrest_count > 0:
                st.warning(f"🚨 AUTOMATED ALERT: Vehicle {vehicle_number} has {arrest_count} prior arrest records.")
            else:
                st.info(f"✅ Vehicle {vehicle_number} has no prior arrests (based on DB).")

            # ensure search_type consistency
            if search_conducted == 0:
                search_type = "No Search"

            new_log = (
                stop_datetime, country_name, vehicle_number, driver_gender, int(driver_age),
                driver_race, violation, stop_duration, stop_outcome, int(search_conducted),
                search_type, int(is_arrested), int(drugs_related_stop)
            )

            try:
                rowid = insert_log(new_log)
                st.success(f"Log recorded successfully (stop_id={rowid}).")
                # refresh KPIs (rudimentary)
                kpis = load_kpis()
                col1.metric("Total Stops", int(kpis["total_stops"]))
            except Exception as e:
                st.error(f"Error recording log: {e}")

st.markdown("---")

# -----------------------
# Section 2: Vehicle Lookup & History
# -----------------------
st.header("🔎 Vehicle Lookup & History")
with st.expander("Search vehicle history"):
    vehicle_lookup = st.text_input("Enter vehicle number to lookup", placeholder="RJ01AB1234").upper().strip()
    if st.button("Lookup Vehicle"):
        if not vehicle_lookup:
            st.error("Enter a vehicle number.")
        else:
            df_hist = run_query(f"SELECT * FROM {TABLE_NAME} WHERE vehicle_number = ? ORDER BY stop_datetime DESC LIMIT 200;", params=[vehicle_lookup])
            if df_hist.empty:
                st.info("No records found for this vehicle.")
            else:
                st.dataframe(df_hist)
                st.download_button("Export Vehicle History CSV", df_hist.to_csv(index=False).encode('utf-8'), file_name=f"{vehicle_lookup}_history.csv")

st.markdown("---")

# -----------------------
# Section 3: Analytics Panel (select query, optional params)
# -----------------------
st.header("📊 Advanced Insights & Crime Pattern Analysis")

selected_query_name = st.selectbox("Select a Pre-defined Analytical Report to Run", list(SQL_QUERIES.keys()))
query_to_run = SQL_QUERIES[selected_query_name]

# Allow user to supply optional parameter filters for some queries
with st.expander("Optional Query Parameters"):
    country_filter = st.text_input("Country name filter (optional)", "")
    min_count = st.number_input("Minimum group size (for HAVING), 0 = use default", min_value=0, value=0)

params = []
# simple param logic for queries that accept a country or min_count -- not all queries use params
if "country_name" in query_to_run and country_filter:
    # naive replacement for demo: filter by country — append WHERE (if not exists) or AND
    if "WHERE" in query_to_run.upper():
        query_to_run = query_to_run.replace("WHERE", "WHERE country_name = ? AND ", 1)
    else:
        query_to_run = query_to_run.replace("GROUP BY", "WHERE country_name = ? GROUP BY", 1)
    params.append(country_filter)

# run the query
if st.button("Run Analytical Query"):
    try:
        df_results = run_query(query_to_run, params=params if params else None)
        if df_results.empty:
            st.info("Query ran successfully but returned no rows.")
        else:
            st.subheader(f"Results for: {selected_query_name}")
            st.dataframe(df_results)

            # simple charting heuristics
            try:
                idx_col = df_results.columns[0]
                st.bar_chart(df_results.set_index(idx_col))
            except Exception:
                st.write("Preview available — charting skipped due to column types.")

            # CSV export
            csv_bytes = df_results.to_csv(index=False).encode('utf-8')
            st.download_button("Export Query Results as CSV", csv_bytes, file_name=f"report_{selected_query_name.replace(' ', '_')}.csv")
    except Exception as e:
        st.error(f"Error running query: {e}. Ensure your DB structure is correct.")

st.markdown("---")

# -----------------------
# Section 4: Quick Charts & Visuals
# -----------------------
st.header("📈 Quick Visuals")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Stops by Hour (Top hours)")
    try:
        df_hours = run_query(SQL_QUERIES["Stops by hour of day"])
        if not df_hours.empty:
            st.bar_chart(df_hours.set_index("hour_of_day"))
        else:
            st.info("No data for hour chart.")
    except Exception as e:
        st.error(f"Hour chart error: {e}")

with col_b:
    st.subheader("Top Vehicles in Drug-related Stops")
    try:
        df_topv = run_query(SQL_QUERIES["Top 10 vehicles in drug-related stops"])
        if not df_topv.empty:
            st.table(df_topv)
        else:
            st.info("No drug-related data.")
    except Exception as e:
        st.error(f"Top vehicles chart error: {e}")

st.markdown("---")

# -----------------------
# Section 5: Admin Utilities (only visible to Admin role in demo)
# -----------------------
if st.session_state.get("role") == "Admin":
    st.header("🛠️ Admin Utilities")
    st.write("DB schema:")
    info = get_table_info()
    st.table([dict(row) for row in info])

    st.write("Danger zone (demo): Recreate DB (drops existing table). Use with caution.")
    if st.button("Recreate table (DROP & CREATE)"):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
            conn.commit()
            init_db()
            st.success("Table recreated. Existing data was removed.")
        except Exception as e:
            st.error(f"Error recreating table: {e}")
        finally:
            conn.close()

st.markdown("---")
st.caption("SecureCheck — Prototype demo. For production: use PostgreSQL/MySQL, secure auth, TLS, and role-based permissions.")
