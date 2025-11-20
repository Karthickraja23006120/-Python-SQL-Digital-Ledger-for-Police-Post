# SecureCheck: A Python-SQL Digital Ledger for Police Post Logs
SecureCheck is a real-time vehicle stop monitoring system built using Python, SQL, and Streamlit.
It replaces manual check-post logging with a centralized and automated digital ledger that helps law enforcement agencies track, analyze, and monitor vehicle movements efficiently.

## Project Overview

- Police check posts require a fast, reliable system for logging vehicle interactions.
SecureCheck provides:

- A clean SQL database for storing vehicle stop data

- Python scripts for data cleaning and preprocessing

- A Streamlit dashboard for real-time visualization

- Automated SQL analytics for violation patterns, arrests, and drug-related stops

 ## Tech Stack
  
-  Python (Pandas, SQLAlchemy)

- SQL (MySQL / PostgreSQL / SQLite)

- Streamlit

- Plotly / Matplotlib

## Project Structure
```
securecheck-police-logs-analysis
├── 1_data_source
│   └── traffic_stops - traffic_stops_with_vehicle_number.csv  (The original, raw data file)
├── 2_data_processing
│   ├── police.py                                            (The cleaning)
│   └── cleaned_traffic_stops.csv                            (The transformed data output)
├── 3_application_and_db
│   ├── app.py                                               (The Streamlit dashboard application)
│   └── securecheck_police_logs.db                           (The SQLite database)
└── README.md

```

## How To Run

### 1) Prerequisites

- Python 3.12

 ### 2)Clone the Repository

 - ```git clone Repo Url ```
 - ```  cd  folder name ```
### 3)Install Dependencies

```pip install pandas streamlit sqlalchemy```

### 4)Data Preparation

``` python police.py ```

### 5)Run the Dashboard Application

``` streamlit run app.py ```
 
