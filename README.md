# SecureCheck: A Python-SQL Digital Ledger for Police Post Logs

## Problem Statement
Police check posts require a centralized system for logging, tracking, and analyzing vehicle movements. Currently, manual logging and inefficient databases slow down security processes. This project aims to build an SQL-based check post database with a Python-powered dashboard for real-time insights and alerts.

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
├── 1_data source
│   └── traffic_stops - traffic_stops_with_vehicle_number.csv  (The original, raw data file)
├── 2_data processing
│   ├── police.py                                            (The cleaning)
│   └── cleaned_traffic_stops.csv                            (The transformed data output)
├── 3_application
│   ├── app.py                                               (The Streamlit dashboard application)
│   └── securecheck_police_logs.db                           (The SQLite database)


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
 
## Output 

<img width="1898" height="883" alt="Screenshot 2025-11-23 220002" src="https://github.com/user-attachments/assets/f86cb686-2516-4bd8-9b52-1f7fb79eb75e" />


<img width="1897" height="899" alt="Screenshot 2025-11-23 220036" src="https://github.com/user-attachments/assets/bcae2dda-dc1d-49a9-aa83-09305f15de82" />


