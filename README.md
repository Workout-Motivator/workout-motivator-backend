# Workout Motivator Backend

![Backend Tests](https://github.com/Workout-Motivator/workout-motivator-backend/actions/workflows/backend-tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/Workout-Motivator/workout-motivator-backend/graph/badge.svg)](https://codecov.io/gh/Workout-Motivator/workout-motivator-backend)
[![CI](https://github.com/Workout-Motivator/workout-motivator-backend/actions/workflows/main.yml/badge.svg)](https://github.com/Workout-Motivator/workout-motivator-backend/actions/workflows/main.yml)
[![Coverage](https://codecov.io/gh/Workout-Motivator/workout-motivator-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/Workout-Motivator/workout-motivator-backend/branch/main)

A FastAPI backend service for the Workout Motivator application. This service handles user management, workout tracking, and partner matching functionality.

## Features

- RESTful API with FastAPI
- PostgreSQL Database Integration
- Firebase Authentication
- Exercise Management
  - Categorized exercises
  - Search and filtering
  - Pagination support
  - Category statistics
- Partner System
  - Partner matching
  - Request management
  - Real-time status updates
- Error Handling
  - Detailed error messages
  - Comprehensive logging
  - Type-safe responses
- Docker Containerization
  - Multi-stage builds
  - Development and production configs
  - Docker Compose support

## Prerequisites

- Python 3.8 or higher
- PostgreSQL
- Docker and Docker Compose (optional)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd workout-motivator/backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/workout_motivator

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase Admin
FIREBASE_ADMIN_SDK_PATH=path/to/firebase-admin-sdk.json

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Project Structure

```
backend/
├── alembic/            # Database migrations
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core functionality
│   ├── crud/          # Database operations
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   └── main.py       # FastAPI application
├── tests/             # Test files
└── requirements.txt   # Python dependencies
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Deployment

1. Build the image:
```bash
docker-compose build
```

2. Start the services:
```bash
docker-compose up -d
```

## Development Guidelines

1. Follow PEP 8 style guide
2. Use type hints
3. Write tests for new features
4. Document API endpoints
5. Use meaningful commit messages

## Testing

Run tests with pytest:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=app tests/
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)
