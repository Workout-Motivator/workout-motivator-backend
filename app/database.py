from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
import psycopg2
from urllib.parse import urlparse

# Create a logger
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@workout-motivator-db:5432/workout_motivator")

# Parse database URL for connection parameters
url = urlparse(SQLALCHEMY_DATABASE_URL)
DB_NAME = url.path[1:]  # Remove leading '/'
DB_USER = url.username
DB_PASSWORD = url.password
DB_HOST = url.hostname
DB_PORT = url.port or 5432

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def recreate_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def init_db(max_retries=5, retry_delay=5):
    logger.info("Initializing database...")
    from time import sleep
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Test database connection
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            conn.close()
            logger.info("Database connection successful")
            
            # Import all models to ensure they are registered with SQLAlchemy
            from . import models
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
            return
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                sleep(retry_delay)
            else:
                raise Exception("Failed to initialize database after maximum retries")
