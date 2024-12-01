from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional
from . import models, schemas
from .database import engine, get_db, recreate_database
from .load_assets import load_assets as load_all_exercise_assets
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Workout Tracker API")

# Configure CORS
origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "Fitness_Assets")
logger.info(f"Mounting static files from: {ASSETS_DIR}")
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)
    logger.info(f"Created assets directory: {ASSETS_DIR}")
app.mount("/static/exercises", StaticFiles(directory=ASSETS_DIR), name="exercises")

@app.on_event("startup")
async def startup_event():
    logger.info("Recreating database tables...")
    recreate_database()
    logger.info("Database tables recreated successfully")

@app.get("/")
async def root():
    return {"message": "Welcome to Workout Tracker API"}

@app.post("/api/workouts/", response_model=schemas.Workout)
def create_workout(workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    db_workout = models.Workout(**workout.dict())
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@app.get("/api/workouts/{user_id}", response_model=List[schemas.Workout])
def get_user_workouts(user_id: str, db: Session = Depends(get_db)):
    workouts = db.query(models.Workout).filter(models.Workout.user_id == user_id).all()
    return workouts

@app.put("/api/workouts/{workout_id}/complete")
def complete_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    workout.completed = True
    db.commit()
    return {"message": "Workout marked as completed"}

@app.get("/api/workouts/assets/categories")
def get_workout_categories(db: Session = Depends(get_db)):
    """Get all unique workout categories"""
    categories = db.query(distinct(models.WorkoutAsset.category)).all()
    return [category[0] for category in categories]

@app.get("/api/workouts/assets", response_model=List[schemas.WorkoutAsset])
def get_workout_assets(db: Session = Depends(get_db)):
    """Get all workout assets"""
    try:
        assets = db.query(models.WorkoutAsset).all()
        return assets
    except Exception as e:
        logger.error(f"Error fetching workout assets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workouts/assets/{asset_id}")
def get_workout_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific workout asset by ID"""
    asset = db.query(models.WorkoutAsset).filter(models.WorkoutAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Workout asset not found")
    return asset

@app.get("/workouts/assets/categories")
async def get_exercise_categories(db: Session = Depends(get_db)):
    # Using distinct and specific column selection for better performance
    categories = db.query(distinct(models.WorkoutAsset.category)).all()
    return [category[0] for category in categories]

@app.get("/workouts/assets/")
async def get_exercises(
    category: str = None,
    search: str = None,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Start with the base query
        query = db.query(models.WorkoutAsset)
        
        # Apply filters
        if category:
            query = query.filter(models.WorkoutAsset.category == category)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(models.WorkoutAsset.title.ilike(search_term))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        exercises = query.offset(offset).limit(limit).all()
        
        # Convert to dict to ensure proper serialization
        exercises_list = []
        for exercise in exercises:
            exercise_dict = {
                "id": exercise.id,
                "title": exercise.title,
                "description": exercise.description,
                "category": exercise.category,
                "difficulty": exercise.difficulty,
                "instructions": exercise.instructions,
                "benefits": exercise.benefits,
                "muscles_worked": exercise.muscles_worked,
                "variations": exercise.variations,
                "image_path": exercise.image_path,
                "animation_path": exercise.animation_path
            }
            exercises_list.append(exercise_dict)
        
        return {
            "exercises": exercises_list,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/admin/load-assets")
async def load_all_assets(db: Session = Depends(get_db)):
    """Admin endpoint to load all exercise assets into the database"""
    try:
        from .load_assets import load_assets
        logger.info("Starting to load assets...")
        load_assets(db)
        logger.info("Assets loaded successfully")
        return {"message": "Assets loaded successfully"}
    except Exception as e:
        logger.error(f"Error loading assets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading assets: {str(e)}"
        )
