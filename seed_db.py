import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, TableDB, CustomerDB
import random

# Connection setup
current_user = os.getenv("USER")
DATABASE_URL = f"postgresql://{current_user}@localhost/dinesync"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed_data():
    print("🧹 Clearing old data...")
    db.query(TableDB).delete()
    db.query(CustomerDB).delete()

    print("🍽️ Seeding 20 Tables...")
    statuses = ["Available", "Occupied", "Dirty"]
    for i in range(1, 21):
        new_table = TableDB(
            table_number=i,
            capacity=random.choice([2, 4, 6, 8]),
            status=random.choice(statuses)
        )
        db.add(new_table)

    print("👥 Seeding 100 Diverse Customers...")
    
    # Diversified Name Pools
    first_names = [
        "Aarav", "Zoya", "Ishaan", "Meera", "Karthik", "Sana", "Pranav", "Ananya",
        "Rohan", "Diya", "Kabir", "Aditi", "Vihaan", "Tara", "Arjun", "Myra",
        "Sai", "Jyothi", "Tenzin", "Fatima", "Deepak", "Riya", "Gautam", "Nila"
    ]
    
    last_names = [
        "Iyer", "Reddy", "Banerjee", "Fernandes", "Khan", "Patel", "Nair", "Deshmukh",
        "Chatterjee", "Menon", "Kulkarni", "Gill", "Bose", "D'Souza", "Rao", "Hegde",
        "Goswami", "Siddiqui", "Pillai", "Chauhan", "Dutta", "Naidu", "Joshi"
    ]
    
    clusters = ["VIP", "Regular", "New", "Churn-Risk"]

    for _ in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        new_customer = CustomerDB(
            name=name,
            total_points=random.randint(0, 5000),
            cluster_tag=random.choice(clusters)
        )
        db.add(new_customer)

    db.commit()
    print("✅ Database successfully populated with 100 diverse records!")

if __name__ == "__main__":
    seed_data()