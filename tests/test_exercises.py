import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Exercise

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture()
def test_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(test_db):
    return TestClient(app)

@pytest.fixture()
def sample_exercises(test_db):
    db = TestingSessionLocal()
    test_exercises = [
        Exercise(
            title="Push-ups",
            description="Basic push-ups exercise",
            category="Strength",
            difficulty="Beginner",
            image_path="pushups.jpg",
            instructions="1. Start in plank position\n2. Lower body\n3. Push up",
            benefits="Builds chest and arm strength",
            muscles_worked="Chest, Triceps, Shoulders",
            variations="Diamond push-ups, Wide push-ups"
        ),
        Exercise(
            title="Advanced Pull-ups",
            description="Advanced pull-ups variation",
            category="Strength",
            difficulty="Advanced",
            image_path="pullups.jpg",
            instructions="1. Hang from bar\n2. Pull up\n3. Lower down",
            benefits="Builds back and arm strength",
            muscles_worked="Back, Biceps",
            variations="Wide grip, Close grip"
        ),
        Exercise(
            title="Running",
            description="Basic cardio exercise",
            category="Cardio",
            difficulty="Beginner",
            image_path="running.jpg",
            instructions="1. Start slow\n2. Maintain pace\n3. Cool down",
            benefits="Improves cardiovascular health",
            muscles_worked="Legs, Core",
            variations="Sprint, Jogging"
        )
    ]
    
    for exercise in test_exercises:
        db.add(exercise)
    db.commit()
    
    yield test_exercises
    db.close()

def test_get_exercises_default_pagination(client, sample_exercises):
    response = client.get("/exercises/")
    assert response.status_code == 200
    data = response.json()
    assert "exercises" in data
    assert "total" in data
    assert len(data["exercises"]) <= 10  # Default limit
    assert data["total"] >= len(data["exercises"])

def test_get_exercises_with_pagination(client, sample_exercises):
    response = client.get("/exercises/?skip=1&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["exercises"]) <= 2

def test_get_exercises_filter_by_category(client, sample_exercises):
    response = client.get("/exercises/?category=Strength")
    assert response.status_code == 200
    data = response.json()
    assert all(exercise["category"] == "Strength" for exercise in data["exercises"])

def test_get_exercises_filter_by_difficulty(client, sample_exercises):
    response = client.get("/exercises/?difficulty=Beginner")
    assert response.status_code == 200
    data = response.json()
    assert all(exercise["difficulty"] == "Beginner" for exercise in data["exercises"])

def test_get_exercises_search(client, sample_exercises):
    response = client.get("/exercises/?search=push")
    assert response.status_code == 200
    data = response.json()
    assert any("push" in exercise["title"].lower() or 
              "push" in exercise["description"].lower() 
              for exercise in data["exercises"])

def test_get_exercise_categories(client, sample_exercises):
    response = client.get("/exercises/categories")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert len(categories) > 0
    assert all(isinstance(cat["category"], str) and 
              isinstance(cat["count"], int) for cat in categories)
    # Verify we have both Strength and Cardio categories
    category_names = [cat["category"] for cat in categories]
    assert "Strength" in category_names
    assert "Cardio" in category_names
