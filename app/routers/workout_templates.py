from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database

router = APIRouter()

@router.post("/", response_model=schemas.WorkoutTemplate)
def create_workout_template(
    workout: schemas.WorkoutTemplateCreate,
    db: Session = Depends(database.get_db)
):
    """
    Create a new workout template using exercises from the exercise library.
    """
    db_workout = models.WorkoutTemplate(**workout.dict())
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@router.get("/", response_model=List[schemas.WorkoutTemplate])
def get_workout_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    """
    Get all workout templates.
    """
    workouts = db.query(models.WorkoutTemplate).offset(skip).limit(limit).all()
    return workouts

@router.get("/{workout_id}", response_model=schemas.WorkoutTemplate)
def get_workout_template(workout_id: int, db: Session = Depends(database.get_db)):
    """
    Get a specific workout template.
    """
    workout = db.query(models.WorkoutTemplate).filter(models.WorkoutTemplate.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout template not found")
    return workout

@router.put("/{workout_id}", response_model=schemas.WorkoutTemplate)
def update_workout_template(
    workout_id: int,
    workout_update: schemas.WorkoutTemplateCreate,
    db: Session = Depends(database.get_db)
):
    """
    Update a workout template.
    """
    workout = db.query(models.WorkoutTemplate).filter(models.WorkoutTemplate.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout template not found")
    
    for key, value in workout_update.dict().items():
        setattr(workout, key, value)
    
    db.commit()
    db.refresh(workout)
    return workout

@router.delete("/{workout_id}")
def delete_workout_template(workout_id: int, db: Session = Depends(database.get_db)):
    """
    Delete a workout template.
    """
    workout = db.query(models.WorkoutTemplate).filter(models.WorkoutTemplate.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout template not found")
    
    db.delete(workout)
    db.commit()
    return {"message": "Workout template deleted successfully"}
