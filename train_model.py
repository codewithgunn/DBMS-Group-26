import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import create_engine
import joblib
import os

# --- DATABASE SETUP ---
current_user = os.getenv("USER")
DATABASE_URL = f"postgresql://{current_user}@localhost/dinesync"
engine = create_engine(DATABASE_URL)

print("🧠 DineSync AI: Loading training data from Postgres...")

# 1. READ FROM THE HISTORICAL DATA TABLE
query = "SELECT day_of_week, hour_of_day, party_size, occupied_tables, waitlist_count, actual_wait_minutes FROM historical_waits"
df = pd.read_sql(query, engine)

print(f"✅ Loaded {len(df)} records for training.")

# 2. DEFINE FEATURES AND TARGET
# Features: [DayOfWeek, HourOfDay, PartySize, OccupiedTables, WaitlistLength]
X = df[['day_of_week', 'hour_of_day', 'party_size', 'occupied_tables', 'waitlist_count']]
y = df['actual_wait_minutes']

# 3. TRAIN A MORE SOPHISTICATED MODEL (Random Forest)
print("🏗️  Training Random Forest Regressor...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. SAVE THE MODEL
joblib.dump(model, "dinesync_brain.pkl")
print("🚀 Model successfully upgraded to RANDOM FOREST!")
print("   - This model now understands peak hours, weekend surges, and party sizes.")

# Example test
test_input = pd.DataFrame([[5, 19, 4, 15, 5]], columns=['day_of_week', 'hour_of_day', 'party_size', 'occupied_tables', 'waitlist_count'])
prediction = model.predict(test_input)[0]
print(f"   - Test Case (Sat @ 7PM, 4 People, Busy): Predicted Wait {prediction:.1f} mins")
