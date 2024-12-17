from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database
from sqlalchemy import func

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedWorkoutAssets)
def get_exercises(
    skip: int = 0,
    limit: int = 10,
    category: str = None,
    difficulty: str = None,
    search: str = None,
    db: Session = Depends(database.get_db)
):
    """
    Get all exercises from the exercise library with filtering options.
    """
    query = db.query(models.Exercise)
    
    if category:
        query = query.filter(models.Exercise.category == category)
    if difficulty:
        query = query.filter(models.Exercise.difficulty == difficulty)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Exercise.title.ilike(search_term)) |
            (models.Exercise.description.ilike(search_term))
        )
    
    total = query.count()
    exercises = query.offset(skip).limit(limit).all()
    
    return {
        "exercises": exercises,
        "total": total,
    }

# Move the categories endpoint above the /{exercise_id} endpoint to prevent path conflict
@router.get("/categories", response_model=List[schemas.CategoryCount])
def get_categories(db: Session = Depends(database.get_db)):
    """
    Get all available exercise categories with counts.
    """
    categories = (
        db.query(
            models.Exercise.category,
            func.count(models.Exercise.id).label("count")
        )
        .group_by(models.Exercise.category)
        .having(models.Exercise.category.isnot(None))
        .all()
    )
    
    return [
        {"category": category, "count": count}
        for category, count in categories
    ]

@router.get("/{exercise_id}", response_model=schemas.WorkoutAssetDetail)
def get_exercise(exercise_id: int, db: Session = Depends(database.get_db)):
    """
    Get detailed information about a specific exercise.
    """
    exercise = db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise
