from app.database import Base, engine
from app.load_assets import init_assets

def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Load all workout assets
    init_assets()
    
    print("Database initialized and assets loaded successfully!")

if __name__ == "__main__":
    init_database()
