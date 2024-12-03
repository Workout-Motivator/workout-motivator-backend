from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from typing import List, Optional
from . import models, schemas
from .database import engine, get_db, recreate_database, init_db
from .load_assets import load_assets as load_all_exercise_assets
from .routers import workouts
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Workout Tracker API")

# Get CORS origins from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workouts.router, prefix="/workouts", tags=["workouts"])

# Mount the exercises directory for serving static files
ASSETS_DIR = Path(__file__).parent / "assets"
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR), html=True), name="assets")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    try:
        # Initialize database tables
        from .database import init_db
        init_db()
        logger.info("Database tables initialized")

        # Check if we have any workout assets
        db = next(get_db())
        try:
            asset_count = db.query(models.WorkoutAsset).count()
            logger.info(f"Found {asset_count} workout assets in database")
            
            if asset_count == 0:
                logger.info("No workout assets found. Loading assets...")
                load_all_exercise_assets(db)
        except Exception as e:
            logger.error(f"Error checking workout assets: {str(e)}")
            raise e
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise e

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

@app.get("/api/workouts/user/{user_id}")
async def get_user_workouts(user_id: str, db: Session = Depends(get_db)):
    try:
        query = """
            SELECT id, title, description, date, completed, user_id
            FROM workouts
            WHERE user_id = %s
            ORDER BY date DESC
        """
        result = db.execute(query, (user_id,))
        workouts = result.fetchall()
        return [dict(row) for row in workouts]
    except Exception as e:
        logger.error(f"Error fetching workouts for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch workouts")

@app.put("/api/workouts/{workout_id}/complete")
async def complete_workout(workout_id: int, db: Session = Depends(get_db)):
    try:
        query = """
            UPDATE workouts
            SET completed = NOT completed
            WHERE id = %s
            RETURNING id, title, description, date, completed, user_id
        """
        result = db.execute(query, (workout_id,))
        db.commit()
        updated_workout = result.fetchone()
        if not updated_workout:
            raise HTTPException(status_code=404, detail="Workout not found")
        return dict(updated_workout)
    except Exception as e:
        logger.error(f"Error toggling workout completion for workout {workout_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update workout")

@app.delete("/api/workouts/{workout_id}")
async def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    try:
        query = "DELETE FROM workouts WHERE id = %s RETURNING id"
        result = db.execute(query, (workout_id,))
        db.commit()
        deleted_workout = result.fetchone()
        if not deleted_workout:
            raise HTTPException(status_code=404, detail="Workout not found")
        return {"message": "Workout deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting workout {workout_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete workout")

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
async def get_workout_asset(asset_id: int, db: Session = Depends(get_db)):
    try:
        query = """
            SELECT 
                id, title, description, category, difficulty,
                instructions, benefits, muscles_worked, variations,
                image_path, animation_path
            FROM workout_assets
            WHERE id = %s
        """
        result = db.execute(query, (asset_id,))
        workout = result.fetchone()
        
        if not workout:
            raise HTTPException(status_code=404, detail="Workout asset not found")
            
        workout_dict = dict(workout)
        
        # Convert image paths to absolute URLs
        if workout_dict['image_path']:
            workout_dict['image_path'] = f"/assets/{workout_dict['image_path'].lstrip('/')}"
        if workout_dict.get('animation_path'):
            workout_dict['animation_path'] = f"/assets/{workout_dict['animation_path'].lstrip('/')}"
            
        return workout_dict
    except Exception as e:
        logger.error(f"Error fetching workout asset {asset_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/workouts/assets/exercise/{title}")
async def get_exercise(title: str, db: Session = Depends(get_db)):
    try:
        from urllib.parse import unquote
        decoded_title = unquote(title)
        
        # Use SQLAlchemy ORM instead of raw SQL
        exercise = db.query(models.WorkoutAsset).filter(
            models.WorkoutAsset.title == decoded_title
        ).first()
        
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
            
        # Convert SQLAlchemy model to dict
        exercise_dict = {
            'id': exercise.id,
            'title': exercise.title,
            'description': exercise.description,
            'category': exercise.category,
            'difficulty': exercise.difficulty,
            'instructions': exercise.instructions,
            'benefits': exercise.benefits,
            'muscles_worked': exercise.muscles_worked,
            'variations': exercise.variations,
            'image_path': exercise.image_path,
            'animation_path': exercise.animation_path
        }
        
        # Convert image paths to absolute URLs
        if exercise_dict['image_path']:
            exercise_dict['image_path'] = f"/assets/{exercise_dict['image_path'].lstrip('/')}"
        if exercise_dict.get('animation_path'):
            exercise_dict['animation_path'] = f"/assets/{exercise_dict['animation_path'].lstrip('/')}"
            
        return exercise_dict
    except Exception as e:
        logger.error(f"Error fetching exercise {title}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/assets/{file_path:path}")
async def serve_asset(file_path: str):
    """Serve static assets with proper content type"""
    # Convert hyphenated path back to spaces for file lookup
    actual_path = file_path.replace("-", " ")
    file_location = os.path.join(ASSETS_DIR, actual_path)
    if not os.path.exists(file_location):
        # Try with original path if converted path doesn't exist
        file_location = os.path.join(ASSETS_DIR, file_path)
        if not os.path.exists(file_location):
            raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(file_location)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
