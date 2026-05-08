import pandas as pd
import sqlite3
import os

print("Starting data processing...")

# Read the CSV
file_path = 'trafficstops.csv'
df = pd.read_csv(file_path)

print(f"Original shape: {df.shape}")

# Step 1: Remove columns that only contain missing values
df.dropna(axis=1, how='all', inplace=True)

# Handle NaN values:
# For numeric, we can fill with median/mean or -1. For categorical, fill with 'Unknown'
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].fillna(value='Unknown')
    else:
        # Instead of generic median, let's just use 0 or drop if few.
        df[col] = df[col].fillna(value=0)

# Replace any lingering tricky missing strings (like "None", although "None" is a valid search type, so let's leave it)

print(f"Cleaned shape: {df.shape}")

# Convert some boolean strings if any to actual strings or bools so SQLite likes it
# In the CSV, they appear as TRUE/FALSE, which pandas parses as string or bool.
for col in ['search_conducted', 'is_arrested', 'drugs_related_stop']:
    if col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.upper() == 'TRUE'

print("Writing to SQLite database...")

# Step 2: Database Design (SQL)
db_path = 'database.db'
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)

# Insert values into SQL
# We'll write the DataFrame to the 'traffic_stops' table
df.to_sql('traffic_stops', conn, if_exists='replace', index=False)

# Optional: Add a simple index for faster queries
cursor = conn.cursor()
cursor.execute("CREATE INDEX idx_is_arrested ON traffic_stops (is_arrested)")
cursor.execute("CREATE INDEX idx_search_conducted ON traffic_stops (search_conducted)")
cursor.execute("CREATE INDEX idx_vehicle_number ON traffic_stops (vehicle_number)")
conn.commit()

conn.close()

print("Data processing complete. Database created successfully.")
