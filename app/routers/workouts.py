from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/assets/", response_model=schemas.PaginatedWorkoutAssets)
def get_workout_assets(
    skip: int = 0,
    limit: int = 10,
    category: str = None,
    difficulty: str = None,
    search: str = None,
    db: Session = Depends(database.get_db)
):
    """
    Get workout assets with filtering options.
    - skip: Number of records to skip for pagination
    - limit: Maximum number of records to return
    - category: Filter by workout category
    - difficulty: Filter by difficulty level
    - search: Search in title and description
    """
    try:
        query = db.query(models.WorkoutAsset)
        
        if category:
            query = query.filter(models.WorkoutAsset.category == category)
        if difficulty:
            query = query.filter(models.WorkoutAsset.difficulty == difficulty)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (models.WorkoutAsset.title.ilike(search_term)) |
                (models.WorkoutAsset.description.ilike(search_term))
            )
        
        total = query.count()
        workouts = query.offset(skip).limit(limit).all()
        
        return {
            "exercises": workouts,
            "total": total,
        }
    except Exception as e:
        logger.error(f"Error fetching workout assets: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching workout assets: {str(e)}"
        )

@router.get("/assets/{workout_id}", response_model=schemas.WorkoutAssetDetail)
def get_workout_asset(workout_id: int, db: Session = Depends(database.get_db)):
    """Get a specific workout asset with detailed information."""
    try:
        workout = db.query(models.WorkoutAsset).filter(models.WorkoutAsset.id == workout_id).first()
        if workout is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workout asset with id {workout_id} not found"
            )
        return workout
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving workout: {str(e)}"
        )

@router.get("/assets/categories")
def get_workout_categories(db: Session = Depends(database.get_db)):
    """Get all available workout categories with counts."""
    try:
        categories = (
            db.query(
                models.WorkoutAsset.category,
                func.count(models.WorkoutAsset.id).label('count')
            )
            .group_by(models.WorkoutAsset.category)
            .filter(models.WorkoutAsset.category.isnot(None))
            .all()
        )
        
        return [{"category": cat, "count": count} for cat, count in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching categories: {str(e)}"
        )

@router.get("/assets/exercise/{title}", response_model=schemas.WorkoutAsset)
def get_exercise(title: str, db: Session = Depends(database.get_db)):
    """Get a specific exercise by title"""
    try:
        logger.info(f"Searching for exercise with title: {title}")
        exercise = db.query(models.WorkoutAsset).filter(
            func.lower(models.WorkoutAsset.title) == func.lower(title)
        ).first()
        
        if not exercise:
            logger.warning(f"Exercise '{title}' not found in database")
            raise HTTPException(
                status_code=404,
                detail=f"Exercise '{title}' not found"
            )
        logger.info(f"Found exercise: {exercise.title} with image path: {exercise.image_path}")
        return exercise
    except Exception as e:
        logger.error(f"Error fetching exercise {title}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching exercise: {str(e)}"
        )

@router.get("/assets/debug/all", response_model=List[schemas.WorkoutAsset])
def get_all_exercises(db: Session = Depends(database.get_db)):
    """Debug endpoint to list all exercises"""
    try:
        exercises = db.query(models.WorkoutAsset).all()
        logger.info(f"Found {len(exercises)} exercises in database")
        for ex in exercises:
            logger.info(f"Exercise: {ex.title}, Category: {ex.category}, Image: {ex.image_path}")
        return exercises
    except Exception as e:
        logger.error(f"Error listing exercises: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing exercises: {str(e)}"
        )

@router.post("/user/", response_model=schemas.Workout)
def create_user_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(database.get_db)
):
    """Create a new workout for the current user."""
    try:
        db_workout = models.Workout(**workout.dict())
        db.add(db_workout)
        db.commit()
        db.refresh(db_workout)
        return db_workout
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating workout: {str(e)}"
        )

@router.get("/user/", response_model=List[schemas.Workout])
def get_user_workouts(
    skip: int = 0,
    limit: int = 100,
    completed: bool = None,
    db: Session = Depends(database.get_db)
):
    """
    Get workouts for the current user with filtering options.
    - completed: Filter by completion status
    """
    try:
        query = db.query(models.Workout)
        
        if completed is not None:
            query = query.filter(models.Workout.completed == completed)
            
        total = query.count()
        workouts = query.order_by(models.Workout.date.desc()).offset(skip).limit(limit).all()
        
        if not workouts:
            status = "completed" if completed else "incomplete" if completed is False else "total"
            raise HTTPException(
                status_code=404,
                detail=f"No {status} workouts found for user"
            )
            
        return workouts
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user workouts: {str(e)}"
        )

@router.put("/user/{workout_id}/complete", response_model=schemas.Workout)
def complete_workout(
    workout_id: int,
    db: Session = Depends(database.get_db)
):
    """Mark a workout as completed."""
    try:
        workout = (
            db.query(models.Workout)
            .filter(models.Workout.id == workout_id)
            .first()
        )
        
        if workout is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workout with id {workout_id} not found"
            )
            
        if workout.completed:
            raise HTTPException(
                status_code=400,
                detail="Workout is already marked as completed"
            )
            
        workout.completed = True
        db.commit()
        db.refresh(workout)
        return workout
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error completing workout: {str(e)}"
        )

@router.delete("/user/{workout_id}", status_code=204)
def delete_workout(
    workout_id: int,
    db: Session = Depends(database.get_db)
):
    """Delete a user's workout."""
    try:
        workout = (
            db.query(models.Workout)
            .filter(models.Workout.id == workout_id)
            .first()
        )
        
        if workout is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workout with id {workout_id} not found"
            )
            
        db.delete(workout)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting workout: {str(e)}"
        )
