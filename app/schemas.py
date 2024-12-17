from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Exercise Library Schemas
class ExerciseBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    instructions: Optional[str] = None
    benefits: Optional[str] = None
    muscles_worked: Optional[str] = None
    variations: Optional[str] = None
    image_path: Optional[str] = None
    animation_path: Optional[str] = None

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True

class WorkoutAssetDetail(Exercise):
    pass

class PaginatedWorkoutAssets(BaseModel):
    exercises: List[Exercise]
    total: int

    class Config:
        orm_mode = True
        from_attributes = True

# Workout Template Schemas
class WorkoutExerciseBase(BaseModel):
    exercise_id: int
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None  # in meters
    notes: Optional[str] = None

class WorkoutExerciseCreate(WorkoutExerciseBase):
    pass

class WorkoutExercise(WorkoutExerciseBase):
    id: int
    exercise: Exercise

    class Config:
        orm_mode = True

class WorkoutTemplateBase(BaseModel):
    title: str
    description: Optional[str] = None
    user_id: str
    difficulty: Optional[str] = None
    estimated_duration: Optional[int] = None  # in minutes

class WorkoutTemplateCreate(WorkoutTemplateBase):
    exercises: List[WorkoutExerciseCreate]

class WorkoutTemplate(WorkoutTemplateBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    exercises: List[WorkoutExercise]

    class Config:
        orm_mode = True

# Workout Tracking Schemas
class WorkoutSetBase(BaseModel):
    exercise_id: int
    set_number: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None  # in meters
    notes: Optional[str] = None

class WorkoutSetCreate(WorkoutSetBase):
    pass

class WorkoutSet(WorkoutSetBase):
    id: int
    completed: bool = False

    class Config:
        orm_mode = True

class WorkoutSessionBase(BaseModel):
    template_id: int
    user_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class WorkoutSessionCreate(WorkoutSessionBase):
    pass

class WorkoutSession(WorkoutSessionBase):
    id: int
    end_time: Optional[datetime] = None
    completed: bool = False
    sets: List[WorkoutSet]

    class Config:
        orm_mode = True

# Utility Schemas
class CategoryCount(BaseModel):
    category: str
    count: int

class PaginatedResponse(BaseModel):
    items: List[Exercise]
    total: int
    page: int
    pages: int

    class Config:
        orm_mode = True
