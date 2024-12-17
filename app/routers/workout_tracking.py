from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from .. import models, schemas, database

router = APIRouter()

@router.post("/start/{workout_id}", response_model=schemas.WorkoutSession)
def start_workout(
    workout_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Start tracking a workout session based on a workout template.
    """
    template = db.query(models.WorkoutTemplate).filter(models.WorkoutTemplate.id == workout_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Workout template not found")
    
    # Create a new workout session for tracking
    workout_session = models.WorkoutSession(
        template_id=template.id,
        user_id=template.user_id,
        start_time=datetime.utcnow(),
        completed=False
    )
    
    db.add(workout_session)
    db.commit()
    db.refresh(workout_session)
    return workout_session

@router.post("/{session_id}/complete", response_model=schemas.WorkoutSession)
def complete_workout(
    session_id: int,
    db: Session = Depends(database.get_db)
):
    """
    Mark a tracked workout session as completed.
    """
    session = db.query(models.WorkoutSession).filter(models.WorkoutSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Workout session not found")
    
    session.completed = True
    session.end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    return session

@router.get("/history", response_model=List[schemas.WorkoutSession])
def get_workout_history(
    skip: int = 0,
    limit: int = 100,
    completed: bool = None,
    db: Session = Depends(database.get_db)
):
    """
    Get workout tracking history with filtering options.
    """
    query = db.query(models.WorkoutSession)
    if completed is not None:
        query = query.filter(models.WorkoutSession.completed == completed)
    
    sessions = query.order_by(models.WorkoutSession.start_time.desc()).offset(skip).limit(limit).all()
    return sessions

@router.get("/stats")
def get_workout_stats(db: Session = Depends(database.get_db)):
    """
    Get workout tracking statistics.
    """
    total_sessions = db.query(models.WorkoutSession).count()
    completed_sessions = db.query(models.WorkoutSession).filter(models.WorkoutSession.completed == True).count()
    
    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0
    }
