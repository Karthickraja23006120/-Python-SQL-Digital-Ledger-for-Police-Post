import pandas as pd

# 1. Load the dataset
file_name = "traffic_stops - traffic_stops_with_vehicle_number.csv"
df = pd.read_csv(file_name)
# Print the initial shape as requested
print("Initial Shape:", df.shape)

# --- Data Cleaning and Transformation ---

# 2. Combine stop_date and stop_time into a single TIMESTAMP column
df['stop_datetime'] = pd.to_datetime(df['stop_date'] + ' ' + df['stop_time'])

# 3. Drop redundant and separate date/time columns
# Also drop the 'raw' columns as the 'cleaned' versions are available and complete
df.drop(columns=['stop_date', 'stop_time', 'driver_age_raw', 'violation_raw'], inplace=True)

# 4. Convert boolean columns (True/False) to integer (1/0) 
# for consistent storage in SQL databases (PostgreSQL, MySQL, SQLite)
bool_cols = ['search_conducted', 'is_arrested', 'drugs_related_stop']
for col in bool_cols:
    # Use .map to be explicit about True/False to 1/0 conversion if data type was object, 
    # but since pandas already inferred bool, astype(int) is cleaner here.
    df[col] = df[col].astype(int) 

# 5. Reorder columns to logically match the planned SQL schema
final_columns = [
    'stop_datetime', 'country_name', 'driver_gender', 'driver_age', 'driver_race',
    'violation', 'search_conducted', 'search_type', 'stop_outcome',
    'is_arrested', 'stop_duration', 'drugs_related_stop', 'vehicle_number'
]
df = df[final_columns]

# 6. Save the cleaned data to a new CSV file
# This is the file you will use to load into your SQL database in Step 2.
df.to_csv("cleaned_traffic_stops.csv", index=False)

print("--- Data Processing Complete ---")
print("Cleaned DataFrame Head:")
try:
    # to_markdown is optional; if not available, fallback to standard print
    print(df.head().to_markdown(index=False, numalign="left", stralign="left"))
except Exception:
    print(df.head())

print("\nCleaned DataFrame Info (Confirming data types):")
# df.info() prints to stdout and returns None; no need to wrap in print()
df.info()