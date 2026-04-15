import os
import datetime
import random
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- MINIMAL MODELS FOR SEEDING ---
Base = declarative_base()

class HistoricalWaitDB(Base):
    __tablename__ = "historical_waits"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    day_of_week = Column(Integer) # 0-6
    hour_of_day = Column(Integer) # 0-23
    party_size = Column(Integer)
    occupied_tables = Column(Integer)
    waitlist_count = Column(Integer)
    actual_wait_minutes = Column(Float)

# Connection setup
current_user = os.getenv("USER")
DATABASE_URL = f"postgresql://{current_user}@localhost/dinesync"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def generate_history():
    print("📊 Generating 1000+ entries of historical dining data...")
    db.query(HistoricalWaitDB).delete()
    
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    data = []

    for day in range(30):
        current_date = start_date + datetime.timedelta(days=day)
        
        # Simulate different hours (11 AM to 11 PM)
        for hour in range(11, 23):
            # Peak hours: 1 PM - 2 PM and 7 PM - 9 PM
            is_peak = (13 <= hour <= 14) or (19 <= hour <= 21)
            is_weekend = current_date.weekday() >= 5
            
            # Number of groups arriving per hour
            num_groups = random.randint(3, 8)
            if is_peak: num_groups += random.randint(5, 12)
            if is_weekend: num_groups += random.randint(4, 8)

            for _ in range(num_groups):
                party_size = random.choice([2, 2, 2, 4, 4, 6])
                
                # Contextual features
                occ_tables = random.randint(5, 15)
                if is_peak: occ_tables = random.randint(15, 20)
                
                wl_count = random.randint(0, 3)
                if is_peak: wl_count = random.randint(4, 10)

                # Ground Truth Wait Time Formula (Base + Factors + Noise)
                # Base 5 mins
                wait = 5.0
                wait += (party_size * 1.5)
                wait += (occ_tables * 2.0)
                wait += (wl_count * 4.0)
                
                if is_weekend: wait *= 1.2
                if is_peak: wait *= 1.3
                
                # Add noise
                wait += random.uniform(-5, 5)
                wait = max(0, wait)

                entry = HistoricalWaitDB(
                    timestamp=current_date.replace(hour=hour, minute=random.randint(0, 59)),
                    day_of_week=current_date.weekday(),
                    hour_of_day=hour,
                    party_size=party_size,
                    occupied_tables=occ_tables,
                    waitlist_count=wl_count,
                    actual_wait_minutes=round(wait, 2)
                )
                db.add(entry)

    db.commit()
    print("✅ Historical data seeded successfully!")

if __name__ == "__main__":
    generate_history()
