from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Text, Table
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    workout_templates = relationship("WorkoutTemplate", back_populates="user")
    workout_sessions = relationship("WorkoutSession", back_populates="user")
    partners = relationship(
        "User",
        secondary=accountability_partners,
        primaryjoin=id==accountability_partners.c.user_id,
        secondaryjoin=id==accountability_partners.c.partner_id,
        backref="partner_users"
    )

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String, index=True)
    difficulty = Column(String, index=True)
    instructions = Column(Text)
    benefits = Column(Text)
    muscles_worked = Column(Text)
    variations = Column(Text)
    image_path = Column(String)
    animation_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    template_exercises = relationship("WorkoutExercise", back_populates="exercise")
    workout_sets = relationship("WorkoutSet", back_populates="exercise")

    def __repr__(self):
        return f"<Exercise {self.title}>"

class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    difficulty = Column(String, index=True)
    estimated_duration = Column(Integer)  # in minutes
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="workout_templates")
    exercises = relationship("WorkoutExercise", back_populates="template", cascade="all, delete-orphan")
    sessions = relationship("WorkoutSession", back_populates="template")

class WorkoutExercise(Base):
    __tablename__ = "workout_template_exercises"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workout_templates.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    duration = Column(Integer)  # in seconds
    distance = Column(Float)    # in meters
    notes = Column(Text)
    order = Column(Integer)     # For exercise order in the workout

    # Relationships
    template = relationship("WorkoutTemplate", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="template_exercises")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("workout_templates.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime)
    completed = Column(Boolean, default=False)
    notes = Column(Text)

    # Relationships
    template = relationship("WorkoutTemplate", back_populates="sessions")
    user = relationship("User", back_populates="workout_sessions")
    sets = relationship("WorkoutSet", back_populates="session", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    set_number = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    duration = Column(Integer)  # in seconds
    distance = Column(Float)    # in meters
    completed = Column(Boolean, default=False)
    notes = Column(Text)

    # Relationships
    session = relationship("WorkoutSession", back_populates="sets")
    exercise = relationship("Exercise", back_populates="workout_sets")
