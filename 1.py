from main import Base, engine

print("⚠️ DELETING OLD DATABASE...")
Base.metadata.drop_all(bind=engine)

print("✨ CREATING NEW TABLES...")
Base.metadata.create_all(bind=engine)

print("✅ DONE! Now restart your main server.")