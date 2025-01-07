from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional
from . import models, schemas
from .database import engine, get_db, recreate_database, init_db, SessionLocal
from .load_assets import load_assets as load_all_exercise_assets
from .routers import exercises, workout_templates, workout_tracking
import logging
import os
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create FastAPI app
app = FastAPI(title="Workout Tracker API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://20.31.46.9", "http://108.141.13.160"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
app.include_router(workout_templates.router, prefix="/workout-templates", tags=["workouts"])
app.include_router(workout_tracking.router, prefix="/workout-tracking", tags=["tracking"])

# Mount assets directory only if it exists
ASSETS_DIR = Path(__file__).parent / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR), html=True), name="assets")
else:
    logger.warning(f"Assets directory {ASSETS_DIR} does not exist. Static file serving is disabled.")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    try:
        # Recreate database tables
        recreate_database()
        
        # Initialize database with exercise assets
        load_all_exercise_assets(SessionLocal())
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/")
async def root():
    return {"message": "Welcome to Workout Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
