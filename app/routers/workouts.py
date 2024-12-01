from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from ..dependencies import get_current_user

router = APIRouter()

@router.get("/assets/", response_model=List[schemas.WorkoutAsset])
def get_workout_assets(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(database.get_db)
):
    """Get all workout assets, optionally filtered by category."""
    query = db.query(models.WorkoutAsset)
    if category:
        query = query.filter(models.WorkoutAsset.category == category)
    return query.offset(skip).limit(limit).all()

@router.get("/assets/{workout_id}", response_model=schemas.WorkoutAssetDetail)
def get_workout_asset(
    workout_id: int,
    db: Session = Depends(database.get_db)
):
    """Get a specific workout asset with its exercises."""
    workout = db.query(models.WorkoutAsset).filter(models.WorkoutAsset.id == workout_id).first()
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout asset not found")
    return workout

@router.get("/assets/categories")
def get_workout_categories(db: Session = Depends(database.get_db)):
    """Get all available workout categories."""
    categories = db.query(models.WorkoutAsset.category).distinct().all()
    return [cat[0] for cat in categories]

# User-specific workout endpoints
@router.post("/user/", response_model=schemas.Workout)
def create_user_workout(
    workout: schemas.WorkoutCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new workout for the current user."""
    db_workout = models.Workout(**workout.dict(), user_id=current_user.id)
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@router.get("/user/", response_model=List[schemas.Workout])
def get_user_workouts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all workouts for the current user."""
    return db.query(models.Workout).filter(
        models.Workout.user_id == current_user.id
    ).offset(skip).limit(limit).all()

@router.put("/user/{workout_id}/complete")
def complete_workout(
    workout_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a workout as completed."""
    workout = db.query(models.Workout).filter(
        models.Workout.id == workout_id,
        models.Workout.user_id == current_user.id
    ).first()
    
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
        
    workout.completed = True
    db.commit()
    return {"status": "success"}
