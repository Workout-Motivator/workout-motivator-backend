from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
import psycopg2
from urllib.parse import quote_plus
from datetime import datetime
import json
from . import models

# Create a logger
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
DB_NAME = os.getenv("POSTGRES_DB", "workout_motivator_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = "workout-motivator-db"
DB_PORT = 5432

# Construct SQLAlchemy URL with proper URL encoding for special characters
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def backup_data(db):
    """Backup existing data before migration"""
    try:
        logger.info("Creating data backup...")
        backup = {
            'exercises': [],
            'workout_templates': [],
            'workout_sessions': []
        }

        # Backup exercises
        exercises = db.query(models.Exercise).all()
        for exercise in exercises:
            backup['exercises'].append({
                'id': exercise.id,
                'title': exercise.title,
                'description': exercise.description,
                'category': exercise.category,
                'difficulty': exercise.difficulty,
                'instructions': exercise.instructions,
                'benefits': exercise.benefits,
                'muscles_worked': exercise.muscles_worked,
                'variations': exercise.variations,
                'image_path': exercise.image_path,
                'animation_path': exercise.animation_path
            })

        # Backup workout templates
        templates = db.query(models.WorkoutTemplate).all()
        for template in templates:
            template_data = {
                'id': template.id,
                'title': template.title,
                'description': template.description,
                'user_id': template.user_id,
                'difficulty': template.difficulty,
                'estimated_duration': template.estimated_duration,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                'exercises': []
            }
            
            for exercise in template.exercises:
                template_data['exercises'].append({
                    'exercise_id': exercise.exercise_id,
                    'sets': exercise.sets,
                    'reps': exercise.reps,
                    'weight': exercise.weight,
                    'duration': exercise.duration,
                    'distance': exercise.distance,
                    'notes': exercise.notes
                })
            
            backup['workout_templates'].append(template_data)

        # Backup workout sessions
        sessions = db.query(models.WorkoutSession).all()
        for session in sessions:
            session_data = {
                'id': session.id,
                'template_id': session.template_id,
                'user_id': session.user_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'completed': session.completed,
                'notes': session.notes,
                'sets': []
            }
            
            for set in session.sets:
                session_data['sets'].append({
                    'exercise_id': set.exercise_id,
                    'set_number': set.set_number,
                    'reps': set.reps,
                    'weight': set.weight,
                    'duration': set.duration,
                    'distance': set.distance,
                    'completed': set.completed,
                    'notes': set.notes
                })
            
            backup['workout_sessions'].append(session_data)

        # Save backup to file
        backup_file = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(backup, f, indent=2)
        
        logger.info(f"Backup created successfully: {backup_file}")
        return backup_file
    
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise

def restore_from_backup(backup_file, db):
    """Restore data from backup file"""
    try:
        logger.info(f"Restoring data from backup: {backup_file}")
        with open(backup_file, 'r') as f:
            backup = json.load(f)

        # Restore exercises
        for exercise_data in backup['exercises']:
            exercise = models.Exercise(**exercise_data)
            db.add(exercise)

        # Restore workout templates
        for template_data in backup['workout_templates']:
            exercises = template_data.pop('exercises')
            template = models.WorkoutTemplate(**template_data)
            
            for exercise_data in exercises:
                template_exercise = models.WorkoutExercise(**exercise_data)
                template.exercises.append(template_exercise)
            
            db.add(template)

        # Restore workout sessions
        for session_data in backup['workout_sessions']:
            sets = session_data.pop('sets')
            session = models.WorkoutSession(**session_data)
            
            for set_data in sets:
                workout_set = models.WorkoutSet(**set_data)
                session.sets.append(workout_set)
            
            db.add(session)

        db.commit()
        logger.info("Data restored successfully")
    
    except Exception as e:
        logger.error(f"Error restoring data: {str(e)}")
        db.rollback()
        raise

def init_db(max_retries=5, retry_delay=5):
    """Initialize the database with retries"""
    retry_count = 0
    last_exception = None

    while retry_count < max_retries:
        try:
            logger.info(f"Attempting database initialization (attempt {retry_count + 1}/{max_retries})")
            
            # Create a new connection for schema operations
            connection = engine.connect()
            connection = connection.execution_options(isolation_level="AUTOCOMMIT")

            # Drop and recreate schema
            connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            logger.info("Database initialized successfully")
            connection.close()
            return True

        except Exception as e:
            last_exception = e
            logger.error(f"Database initialization attempt {retry_count + 1} failed: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                import time
                time.sleep(retry_delay)

    logger.error(f"Database initialization failed after {max_retries} attempts")
    raise last_exception

def recreate_database():
    """Recreate all database tables with proper handling of dependencies."""
    try:
        logger.info("Recreating database tables...")
        init_db(max_retries=5, retry_delay=5)
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}")
        raise

def verify_database_integrity():
    """Verify database integrity after migration"""
    try:
        db = SessionLocal()
        
        # Check if tables exist
        inspector = inspect(engine)
        required_tables = {'exercise', 'workout_template', 'workout_session', 'workout_set'}
        existing_tables = set(inspector.get_table_names())
        
        if not required_tables.issubset(existing_tables):
            missing_tables = required_tables - existing_tables
            raise Exception(f"Missing tables: {missing_tables}")
        
        # Verify data consistency
        exercise_count = db.query(models.Exercise).count()
        template_count = db.query(models.WorkoutTemplate).count()
        session_count = db.query(models.WorkoutSession).count()
        
        logger.info(f"Database integrity verified:")
        logger.info(f"- Exercises: {exercise_count}")
        logger.info(f"- Workout Templates: {template_count}")
        logger.info(f"- Workout Sessions: {session_count}")
        
        return True
    
    except Exception as e:
        logger.error(f"Database integrity verification failed: {str(e)}")
        raise
    
    finally:
        db.close()

def migrate_data():
    """Migrate data from old schema to new schema if needed"""
    logger.info("Checking if data migration is needed...")
    db = SessionLocal()
    backup_file = None
    
    try:
        # Check if old tables exist
        inspector = inspect(engine)
        has_old_schema = (
            'workout_assets' in inspector.get_table_names() and
            'exercise_assets' in inspector.get_table_names()
        )

        if has_old_schema:
            logger.info("Old schema detected. Starting data migration...")
            
            # Create backup before migration
            backup_file = backup_data(db)
            
            # Create a mapping of old exercise IDs to new ones
            exercise_id_mapping = {}
            
            # Migrate workout assets to exercises
            old_assets = db.query(models.WorkoutAsset).all()
            for asset in old_assets:
                new_exercise = models.Exercise(
                    title=asset.title,
                    description=asset.description,
                    category=asset.category,
                    difficulty=asset.difficulty,
                    instructions=asset.instructions,
                    benefits=asset.benefits,
                    muscles_worked=asset.muscles_worked,
                    variations=asset.variations,
                    image_path=asset.image_path,
                    animation_path=asset.animation_path
                )
                db.add(new_exercise)
                db.flush()  # Get the new ID
                exercise_id_mapping[asset.id] = new_exercise.id
            
            # Migrate workouts to workout templates
            old_workouts = db.query(models.Workout).all()
            for workout in old_workouts:
                new_template = models.WorkoutTemplate(
                    title=workout.title,
                    description=workout.description,
                    user_id=workout.user_id,
                    created_at=workout.created_at,
                    updated_at=workout.updated_at
                )
                db.add(new_template)
                db.flush()
                
                # Migrate workout exercises to template exercises
                for old_exercise in workout.exercises:
                    template_exercise = models.WorkoutExercise(
                        template_id=new_template.id,
                        exercise_id=exercise_id_mapping.get(old_exercise.id),
                        sets=old_exercise.sets,
                        reps=old_exercise.reps,
                        weight=old_exercise.weight,
                        duration=old_exercise.duration,
                        distance=old_exercise.distance
                    )
                    db.add(template_exercise)
                
                # Create a session for completed workouts
                if workout.completed:
                    session = models.WorkoutSession(
                        template_id=new_template.id,
                        user_id=workout.user_id,
                        start_time=workout.date,
                        end_time=workout.updated_at,
                        completed=True
                    )
                    db.add(session)
            
            db.commit()
            logger.info("Data migration completed successfully")

    except Exception as e:
        logger.error(f"Error during data migration: {str(e)}")
        db.rollback()
        
        # Attempt to restore from backup if available
        if backup_file:
            logger.info("Attempting to restore from backup...")
            try:
                recreate_database()  # Reset to clean state
                restore_from_backup(backup_file, db)
                logger.info("Successfully restored from backup")
            except Exception as restore_error:
                logger.error(f"Failed to restore from backup: {str(restore_error)}")
                raise Exception(f"Migration failed and restore failed: {str(e)}\nRestore error: {str(restore_error)}")
        raise
    finally:
        db.close()
