# SecureCheck: Police Post Ledger

## Overview
**SecureCheck** is an end-to-end Python-SQL Digital Ledger designed specifically for police check post and law enforcement operations. By centralizing reporting, search logs, and vehicle tracing, the system effectively moves manual and inefficient operations into an optimized, robust, and real-time environment.

## Project Architecture
This project leverages **Python** for preprocessing, **SQLite** for maintaining database constraints and integrity, and **Streamlit** to offer a responsive, real-time tracking interface combined with interactive Plotly analytics.

### Key Components:
- **`data_processing.py`**: A python pipeline that loads data, handles missing inputs, standardizes fields, builds optimal database indexes, and securely transacts structured logic into the SQL ledger (`database.db`).
- **`app.py`**: The Streamlit user interface featuring a modern, premium dark aesthetic (Glassmorphism design). It includes three main functional aspects:
  1. **Live Check Post Operations**: Logs lookup mechanism built via SQL querying enabling pinpoint search (e.g. by vehicle, reason).
  2. **Data-Backed Decision Analytics**: Visual mapping of time-based incidents and country distributions.
  3. **SQL Reporting Engine**: Embedded exact answers to the requested intermediate and complex questions from the problem statement, executed instantly.

## Running the Application Locally

### Prerequisites
Make sure you have your Python environment set up with all dependencies installed.
```shell
# Activate your virtual environment (if used)
.\.venv\Scripts\Activate.ps1

# Ensure dependencies are installed
pip install pandas streamlit plotly
```

### Steps to Run
1. **Initialize the Database Ledger**
Run the data processor script to read the `trafficstops.csv`, clean the variables, and populate `database.db`.
```shell
python data_processing.py
```

2. **Launch SecureCheck Dashboard**
Start up the Streamlit interface:
```shell
streamlit run app.py
```

Once running, the application will boot on your local server (`http://localhost:8501`) and you can navigate the real-time insights immediately.
