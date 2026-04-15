# seed.py
from sqlalchemy.orm import sessionmaker
from main import TableDB, CustomerDB, engine

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed_data():
    # 1. Add Tables (only if they don't exist)
    for i in range(1, 11):  # Creating 10 tables
        exists = db.query(TableDB).filter(TableDB.table_number == i).first()
        if not exists:
            db.add(TableDB(
                table_number=i, 
                capacity=2 if i < 5 else 4 if i < 9 else 8, 
                status="Available"
            ))

    # 2. Add a Sample VIP Customer (only if they don't exist)
    cust_exists = db.query(CustomerDB).filter(CustomerDB.email == "john@example.com").first()
    if not cust_exists:
        db.add(CustomerDB(
            name="John Doe", 
            email="john@example.com", 
            phone="9876543210", 
            total_points=150, 
            cluster_tag="VIP"
        ))

    try:
        db.commit()
        print("✅ Database check complete! Tables and customers are ready.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()