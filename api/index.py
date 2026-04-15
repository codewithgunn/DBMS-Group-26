import os
import datetime
import random
from datetime import timedelta
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from fastapi.middleware.cors import CORSMiddleware
import joblib

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL"))
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Add connection pooling parameters for serverless
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    elif "sslmode" not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"

logger.info(f"Connecting to database: {DATABASE_URL.split('@')[-1] if DATABASE_URL else 'None'}")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"Failed to create engine: {e}")
    raise e

# --- MODELS ---
# ... (rest of models remain the same) ...

class CustomerDB(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, unique=True, index=True)
    total_points = Column(Integer, default=0)
    visit_count = Column(Integer, default=1)
    cluster_tag = Column(String, default="New")
    reservations = relationship("ReservationDB", back_populates="customer")
    bills = relationship("BillDB", back_populates="customer")

class TableDB(Base):
    __tablename__ = "tables"
    table_id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, unique=True)
    capacity = Column(Integer)
    status = Column(String, default="Available") 
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class ReservationDB(Base):
    __tablename__ = "reservations"
    reservation_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    table_id = Column(Integer, ForeignKey("tables.table_id"), nullable=True)
    reservation_time = Column(DateTime)
    party_size = Column(Integer)
    status = Column(String, default="Confirmed")
    customer = relationship("CustomerDB", back_populates="reservations")

class WaitlistDB(Base):
    __tablename__ = "waitlist" 
    waitlist_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    party_size = Column(Integer)
    phone = Column(String)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    estimated_wait_minutes = Column(Integer, default=0)

class BillDB(Base):
    __tablename__ = "bills"
    bill_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=True)
    table_id = Column(Integer, ForeignKey("tables.table_id"))
    subtotal = Column(Float)
    loyalty_discount = Column(Float, default=0.0)
    final_total = Column(Float)
    payment_status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    customer = relationship("CustomerDB", back_populates="bills")

class LoyaltyRedemptionDB(Base):
    __tablename__ = "loyalty_redemptions"
    redemption_id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.bill_id"))
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    points_redeemed = Column(Integer)
    discount_amount = Column(Float)
    redeemed_at = Column(DateTime, default=datetime.datetime.utcnow)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- HELPER: UPGRADED SMART TIME PREDICTION ALGO ---
def calculate_smart_wait(db: Session, party_size: int):
    # 1. Dynamic Dining Times
    if party_size <= 2:
        target_capacity = 2
        avg_dining_time = 45
    elif party_size <= 4:
        target_capacity = 4
        avg_dining_time = 60
    else:
        target_capacity = 6
        avg_dining_time = 75

    CLEANING_BUFFER = 5 

    tables = db.query(TableDB).filter(TableDB.capacity == target_capacity).all()
    if not tables:
        return 99 

    people_ahead = 0
    waitlist = db.query(WaitlistDB).all()
    for w in waitlist:
        if (w.party_size <= 2 and target_capacity == 2) or \
           (2 < w.party_size <= 4 and target_capacity == 4) or \
           (w.party_size > 4 and target_capacity == 6):
            people_ahead += 1

    timeline = []
    now = datetime.datetime.utcnow()
    
    for t in tables:
        if t.status == "Available":
            timeline.append(0)
        elif t.status == "Dirty":
            timeline.append(CLEANING_BUFFER)
        else: # Occupied
            elapsed_minutes = (now - t.last_updated).total_seconds() / 60
            remaining = max(0, avg_dining_time - elapsed_minutes)
            timeline.append(remaining + CLEANING_BUFFER)
            
    timeline.sort()

    num_tables = len(timeline)
    if num_tables == 0: return 15
    
    table_index = people_ahead % num_tables
    cycles = people_ahead // num_tables
    
    cycle_time = avg_dining_time + CLEANING_BUFFER
    base_prediction = timeline[table_index] + (cycles * cycle_time)

    # 6. AI Refinement (Random Forest)
    try:
        model_path = os.path.join(os.path.dirname(__file__), "..", "dinesync_brain.pkl")
        if os.path.exists(model_path):
            import pandas as pd
            model = joblib.load(model_path)
            
            now_dt = datetime.datetime.now()
            total_occupied = db.query(TableDB).filter(TableDB.status == "Occupied").count()
            
            test_input = pd.DataFrame([[
                now_dt.weekday(),     # day_of_week
                now_dt.hour,          # hour_of_day
                party_size,        # party_size
                total_occupied,    # occupied_tables
                people_ahead       # waitlist_count
            ]], columns=['day_of_week', 'hour_of_day', 'party_size', 'occupied_tables', 'waitlist_count'])
            
            ai_prediction = model.predict(test_input)[0]
            final_wait = (base_prediction * 0.6) + (ai_prediction * 0.4)
            return int(final_wait)
    except Exception as e:
        print(f"⚠️ AI Prediction Skip: {e}")

    return int(base_prediction)

# --- INITIALIZATION ---
@app.on_event("startup")
def startup_event():
    logger.info("Application starting up...")
    try:
        # Only create tables if they don't exist, don't drop!
        Base.metadata.create_all(bind=engine)
        logger.info("Tables checked/created successfully.")
        
        db = SessionLocal()
        # Basic seed if empty
        if db.query(TableDB).count() == 0:
            logger.info("🌱 Initial Table Seeding...")
            tables = []
            for i in range(1, 21):
                cap = 2 if i <= 8 else 4 if i <= 16 else 6
                tables.append(TableDB(table_number=i, capacity=cap, status="Available"))
            db.add_all(tables)
            db.commit()
            logger.info("Seeding completed.")
        db.close()
    except Exception as e:
        logger.error(f"❌ Critical Error during startup: {e}")
        # In serverless, we might not want to raise if we want the app to at least serve 
        # a basic status, but for debugging, we need to know it failed.
        raise e

# --- ENDPOINTS ---

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    tables = db.query(TableDB).order_by(TableDB.table_number).all()
    waitlist = db.query(WaitlistDB).order_by(WaitlistDB.joined_at).all()
    customers = db.query(CustomerDB).order_by(CustomerDB.total_points.desc()).all()
    recent_bills = db.query(BillDB).order_by(BillDB.created_at.desc()).limit(10).all()
    
    bill_data = []
    for b in recent_bills:
        c_name = b.customer.name if b.customer else "Guest"
        bill_data.append({"id": b.bill_id, "customer": c_name, "total": b.final_total, "status": b.payment_status, "created_at": b.created_at})

    occupied = sum(1 for t in tables if t.status == 'Occupied')
    occ_rate = f"{int((occupied / len(tables)) * 100)}%" if tables else "0%"
    
    wait_times = {str(s): calculate_smart_wait(db, s) for s in [2, 4, 6]}
    
    segment_counts = {}
    for c in customers:
        tag = c.cluster_tag or "New"
        segment_counts[tag] = segment_counts.get(tag, 0) + 1
    chart_data = [{"name": k, "value": v} for k, v in segment_counts.items()] or [{"name": "No Data", "value": 1}]

    return {
        "tables": tables,
        "waitlist": waitlist,
        "recent_bills": bill_data,
        "occupancy_rate": occ_rate,
        "wait_times_detailed": wait_times,
        "customer_list": customers,
        "chart_data": chart_data
    }

@app.get("/api/customers")
def get_customers(search: str = "", tag: str = "All", db: Session = Depends(get_db)):
    query = db.query(CustomerDB)
    if search:
        query = query.filter(or_(CustomerDB.name.ilike(f"%{search}%"), CustomerDB.phone.ilike(f"%{search}%")))
    if tag and tag != "All":
        query = query.filter(CustomerDB.cluster_tag == tag)
    return query.order_by(CustomerDB.total_points.desc()).all()

@app.post("/api/queue/add")
def add_to_waitlist(name: str, size: int, phone: str, db: Session = Depends(get_db)):
    est_wait = calculate_smart_wait(db, size)
    db.add(WaitlistDB(customer_name=name, party_size=size, phone=phone, estimated_wait_minutes=est_wait))
    db.commit()
    return {"message": "Added"}

@app.post("/api/queue/seat/{waitlist_id}")
def seat_guest(waitlist_id: int, db: Session = Depends(get_db)):
    guest = db.query(WaitlistDB).filter(WaitlistDB.waitlist_id == waitlist_id).first()
    if not guest: return {"error": "Guest not found"}
    table = db.query(TableDB).filter(TableDB.status == "Available", TableDB.capacity >= guest.party_size).first()
    if not table: return {"error": f"No Available Table for size {guest.party_size}"}
    table.status = "Occupied"
    table.last_updated = datetime.datetime.utcnow()
    db.delete(guest)
    db.commit()
    return {"message": f"Seated at Table {table.table_number}"}

@app.post("/api/tables/{table_id}/pay")
def pay_bill(table_id: int, amount: float, phone: str, name: str = "Guest", db: Session = Depends(get_db)):
    table = db.query(TableDB).filter(TableDB.table_id == table_id).first()
    clean_phone = phone.strip()
    customer = db.query(CustomerDB).filter(CustomerDB.phone == clean_phone).first()
    if not customer:
        customer = CustomerDB(name=name, phone=clean_phone, total_points=0, visit_count=0, cluster_tag="New")
        db.add(customer)
        db.flush() 
    else:
        if name != "Guest": customer.name = name
    points_earned = int(amount * 0.10)
    customer.total_points += points_earned
    customer.visit_count += 1
    if customer.total_points > 1000: customer.cluster_tag = "VIP"
    elif customer.visit_count > 5: customer.cluster_tag = "Regular"
    else: customer.cluster_tag = "New"
    new_bill = BillDB(customer_id=customer.customer_id, table_id=table_id, subtotal=amount, final_total=amount, payment_status="Paid")
    table.status = "Dirty" 
    db.add(new_bill)
    db.commit()
    return {"message": "Paid", "points_earned": points_earned}

@app.post("/api/tables/{table_id}/clean")
def clean_table(table_id: int, db: Session = Depends(get_db)):
    table = db.query(TableDB).filter(TableDB.table_id == table_id).first()
    table.status = "Available"
    db.commit()
    return {"message": "Table Cleaned"}
