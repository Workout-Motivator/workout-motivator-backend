from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WorkoutBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    completed: bool = False
    user_id: str

class WorkoutCreate(WorkoutBase):
    pass

class Workout(WorkoutBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class WorkoutAssetBase(BaseModel):
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

class WorkoutAssetCreate(WorkoutAssetBase):
    pass

class WorkoutAsset(WorkoutAssetBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True

class WorkoutAssetDetail(WorkoutAsset):
    exercise_assets: List['ExerciseAsset'] = []

class ExerciseBase(BaseModel):
    title: str
    description: Optional[str] = None
    workout_id: int
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None  # in meters

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

class ExerciseAsset(BaseModel):
    id: int
    title: str
    instructions: Optional[str] = None
    benefits: Optional[str] = None
    image_paths: Optional[str] = None
    workout_id: int

    class Config:
        orm_mode = True

class CategoryCount(BaseModel):
    category: str
    count: int

class PaginatedWorkoutAssets(BaseModel):
    exercises: List[WorkoutAsset]
    total: int

    class Config:
        orm_mode = True
        from_attributes = True

# Update forward references
WorkoutAssetDetail.update_forward_refs()
