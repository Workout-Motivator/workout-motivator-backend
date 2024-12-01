from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Table
from sqlalchemy.orm import relationship
from .database import Base
import datetime

# Association table for accountability partnerships
accountability_partners = Table(
    'accountability_partners',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('partner_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    workouts = relationship("Workout", back_populates="user")
    partners = relationship(
        "User",
        secondary=accountability_partners,
        primaryjoin=id==accountability_partners.c.user_id,
        secondaryjoin=id==accountability_partners.c.partner_id,
        backref="partner_users"
    )

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="workouts")
    exercises = relationship("Exercise", back_populates="workout")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    workout_id = Column(Integer, ForeignKey("workouts.id"))

    workout = relationship("Workout", back_populates="exercises")

class WorkoutAsset(Base):
    __tablename__ = "workout_assets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    difficulty = Column(String)
    instructions = Column(Text)
    benefits = Column(Text)
    muscles_worked = Column(Text)
    variations = Column(Text)
    image_path = Column(String)
    animation_path = Column(String)
    
    exercise_assets = relationship("ExerciseAsset", back_populates="workout")

    def __repr__(self):
        return f"<WorkoutAsset(id={self.id}, title='{self.title}', category='{self.category}')>"

class ExerciseAsset(Base):
    __tablename__ = "exercise_assets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    instructions = Column(String)
    benefits = Column(String)
    image_paths = Column(String)  # JSON string containing array of image paths
    workout_id = Column(Integer, ForeignKey("workout_assets.id"))
    workout = relationship("WorkoutAsset", back_populates="exercise_assets")
