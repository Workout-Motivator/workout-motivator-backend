from pydantic import BaseModel
from typing import Optional, List

class WorkoutBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    completed: bool = False
    user_id: str

class WorkoutCreate(WorkoutBase):
    pass

class Workout(WorkoutBase):
    id: int

    class Config:
        orm_mode = True

class WorkoutAssetBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    difficulty: str
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

class ExerciseBase(BaseModel):
    title: str
    description: Optional[str] = None
    workout_id: int

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    id: int

    class Config:
        orm_mode = True
