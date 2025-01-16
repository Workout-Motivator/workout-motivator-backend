import pytest
import os
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import database, load_assets, models
from datetime import datetime

# Test database configuration
TEST_DB_NAME = "test_workout_motivator_db"
TEST_DB_USER = "postgres"
TEST_DB_PASSWORD = "admin"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = 5432

# Create test database URL
TEST_DATABASE_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL)
    return engine

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database tables and return a session."""
    models.Base.metadata.create_all(bind=test_engine)
    session = Session(test_engine)
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=test_engine)

def test_database_initialization(test_db):
    """Test database initialization process."""
    # Test if we can connect to the database
    assert test_db is not None
    
    # Test if we can create a new exercise
    exercise = models.Exercise(
        title="Test Exercise",
        description="Test Description",
        category="Test",
        difficulty="beginner",
        instructions="Test instructions",
        benefits="Test benefits",
        muscles_worked="Test muscles",
        variations="Test variations"
    )
    test_db.add(exercise)
    test_db.commit()
    
    # Verify exercise was created
    saved_exercise = test_db.query(models.Exercise).filter_by(title="Test Exercise").first()
    assert saved_exercise is not None
    assert saved_exercise.title == "Test Exercise"

def test_backup_and_restore(test_db):
    """Test database backup and restore functionality."""
    # Create test data
    exercise = models.Exercise(
        title="Backup Test Exercise",
        description="Test Description",
        category="Test",
        difficulty="intermediate"
    )
    test_db.add(exercise)
    test_db.commit()
    
    # Create backup
    backup_file = database.backup_data(test_db)
    assert os.path.exists(backup_file)
    
    # Clear database
    test_db.query(models.Exercise).delete()
    test_db.commit()
    
    # Verify data is cleared
    assert test_db.query(models.Exercise).count() == 0
    
    # Restore from backup
    database.restore_from_backup(backup_file, test_db)
    
    # Verify data is restored
    restored_exercise = test_db.query(models.Exercise).first()
    assert restored_exercise is not None
    assert restored_exercise.title == "Backup Test Exercise"
    
    # Clean up backup file
    os.remove(backup_file)

def test_load_assets_functionality(test_db, tmp_path):
    """Test asset loading functionality with temporary test assets."""
    # Create temporary asset structure
    assets_dir = tmp_path / "assets"
    category_dir = assets_dir / "Test_Exercises"
    exercise_dir = category_dir / "Test Exercise"
    exercise_dir.mkdir(parents=True)
    
    # Create test metadata.json
    metadata = {
        "title": "Test Exercise",
        "description": "Test Description",
        "difficulty": "Beginner",
        "content": [
            {
                "type": "section",
                "title": "Instructions",
                "content": {"type": "steps", "items": ["Step 1", "Step 2"]}
            }
        ]
    }
    
    with open(exercise_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)
    
    # Create test image
    with open(exercise_dir / "image.jpg", "w") as f:
        f.write("test image content")
    
    # Monkey patch the assets directory path
    original_path = Path(load_assets.__file__).parent / "assets"
    load_assets.__file__ = str(tmp_path / "load_assets.py")
    
    try:
        # Load assets
        load_assets.load_assets(test_db)
        
        # Verify exercise was loaded
        exercise = test_db.query(models.Exercise).first()
        assert exercise is not None
        assert exercise.title == "Test Exercise"
        assert exercise.category == "Test"
        assert exercise.difficulty == "Beginner"
        assert exercise.image_path is not None
    finally:
        # Restore original path
        load_assets.__file__ = str(original_path.parent / "load_assets.py")

def test_database_integrity(test_db):
    """Test database integrity checks and constraints."""
    # Test unique title constraint
    exercise1 = models.Exercise(
        title="Unique Test",
        description="Test 1",
        category="Test"
    )
    test_db.add(exercise1)
    test_db.commit()
    
    # Try to add exercise with same title
    exercise2 = models.Exercise(
        title="Unique Test",
        description="Test 2",
        category="Test"
    )
    test_db.add(exercise2)
    
    # Should raise an integrity error
    with pytest.raises(Exception):
        test_db.commit()
    test_db.rollback()
    
    # Test cascade delete
    template = models.WorkoutTemplate(
        title="Test Template",
        description="Test Description",
        user_id="test_user",
        difficulty="beginner"
    )
    test_db.add(template)
    test_db.commit()
    
    # Add workout session linked to template
    session = models.WorkoutSession(
        template_id=template.id,
        user_id="test_user",
        start_time=datetime.now()
    )
    test_db.add(session)
    test_db.commit()
    
    # Delete template and verify cascade
    test_db.delete(template)
    test_db.commit()
    
    # Verify session was also deleted
    assert test_db.query(models.WorkoutSession).filter_by(id=session.id).first() is None
