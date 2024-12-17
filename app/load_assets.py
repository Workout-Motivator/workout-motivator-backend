import os
import json
import shutil
from sqlalchemy.orm import Session
from . import models, database
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def clean_html_content(content: Dict[str, Any]) -> str:
    """Extract clean text content from the content dictionary."""
    if not content:
        return ""
    
    if isinstance(content, str):
        return content.strip()
    
    if isinstance(content, dict):
        if "items" in content:
            if content.get("type") == "steps":
                return "\n".join(f"{i+1}. {item}" for i, item in enumerate(content["items"]))
            else:
                return "\n".join(f"• {item}" for item in content["items"])
    
    return ""

def extract_content_by_title(content_data: Dict[str, Any], title: str) -> str:
    """Extract specific content section by title from the content array."""
    for item in content_data.get("content", []):
        if item.get("type") == "section" and item.get("title") == title:
            return clean_html_content(item.get("content", ""))
    return ""

def find_image_paths(exercise_dir: Path) -> tuple[Optional[str], Optional[str]]:
    """Find image and animation files in the exercise directory.
    
    Returns:
        tuple: (image_path, animation_path) where paths are relative to the assets directory
               and use forward slashes for consistency
    """
    image_path = None
    animation_path = None
    
    # Get category and exercise names from path and replace spaces with hyphens
    category = exercise_dir.parent.name.replace(" ", "-")
    exercise_name = exercise_dir.name.replace(" ", "-")
    
    for file in exercise_dir.iterdir():
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            # Store path relative to assets directory with forward slashes and replace spaces
            if not image_path:
                image_path = f"/assets/exercises/{category}/{exercise_name}/{file.name.replace(' ', '-')}"
        elif file.suffix.lower() in ['.gif']:
            animation_path = f"/assets/exercises/{category}/{exercise_name}/{file.name.replace(' ', '-')}"
    
    return image_path, animation_path

def load_exercise_assets(db: Session, category_dir: Path, category: str):
    """Load exercise assets from a category directory."""
    if not category_dir.exists():
        logger.warning(f"Category directory not found: {category_dir}")
        return

    for exercise_dir in category_dir.iterdir():
        if not exercise_dir.is_dir():
            continue

        content_file = exercise_dir / "content.json"
        if not content_file.exists():
            logger.warning(f"No content.json found in {exercise_dir}")
            continue

        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                content_data = json.load(f)

            # Extract content sections
            title = content_data.get("title", exercise_dir.name)
            instructions = extract_content_by_title(content_data, f"{title} Instructions")
            benefits = extract_content_by_title(content_data, f"{title} Benefits")
            muscles = extract_content_by_title(content_data, f"{title} Muscles Worked")
            variations = extract_content_by_title(content_data, f"{title} Variations & Alternatives")
            description = extract_content_by_title(content_data, f"{title} Form & Visual")

            # Find image files
            image_path, animation_path = find_image_paths(exercise_dir)

            # Create exercise
            exercise = models.Exercise(
                title=title,
                description=description,
                category=category.replace("_Exercises", "").strip(),
                difficulty="intermediate",  # Default difficulty
                instructions=instructions,
                benefits=benefits,
                muscles_worked=muscles,
                variations=variations,
                image_path=image_path,
                animation_path=animation_path
            )

            # Add to database
            db.add(exercise)
            db.commit()
            logger.info(f"Added exercise: {title}")

        except Exception as e:
            logger.error(f"Error loading exercise from {exercise_dir}: {str(e)}")
            db.rollback()

def load_assets(db: Session):
    """Load all fitness assets into the database."""
    logger.info("Starting asset loading process...")
    
    # Get the assets directory path
    assets_dir = Path(__file__).parent / "assets"
    
    if not assets_dir.exists():
        logger.warning(f"Assets directory not found: {assets_dir}")
        return
    
    try:
        # Process each category directory
        for category_dir in assets_dir.iterdir():
            if category_dir.is_dir():
                # Convert directory name to category format (e.g., "Cardio_Exercises" -> "Cardio")
                category = category_dir.name.replace("_Exercises", "")
                logger.info(f"Processing category: {category}")
                
                # Process exercises in this category
                for exercise_dir in category_dir.iterdir():
                    if exercise_dir.is_dir():
                        try:
                            # Load the exercise metadata
                            metadata_file = exercise_dir / "metadata.json"
                            if not metadata_file.exists():
                                logger.warning(f"No metadata.json found in {exercise_dir}")
                                continue
                            
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)
                            
                            # Find image and animation paths
                            image_path, animation_path = find_image_paths(exercise_dir)
                            
                            # Extract content sections
                            content_data = metadata.get("content", {})
                            instructions = extract_content_by_title(metadata, "Instructions")
                            benefits = extract_content_by_title(metadata, "Benefits")
                            muscles_worked = extract_content_by_title(metadata, "Primary Muscles")
                            variations = extract_content_by_title(metadata, "Variations")
                            
                            # Create or update exercise in database
                            exercise = db.query(models.Exercise).filter(
                                models.Exercise.title == metadata.get("title")
                            ).first()
                            
                            if not exercise:
                                exercise = models.Exercise(
                                    title=metadata.get("title"),
                                    description=metadata.get("description", ""),
                                    category=category,
                                    difficulty=metadata.get("difficulty", "Beginner"),
                                    instructions=instructions,
                                    benefits=benefits,
                                    muscles_worked=muscles_worked,
                                    variations=variations,
                                    image_path=image_path,
                                    animation_path=animation_path
                                )
                                db.add(exercise)
                                logger.info(f"Added exercise: {exercise.title}")
                            else:
                                logger.info(f"Exercise already exists: {exercise.title}")
                            
                        except Exception as e:
                            logger.error(f"Error processing exercise {exercise_dir}: {str(e)}")
                            continue
                
        db.commit()
        logger.info("Asset loading completed successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading assets: {str(e)}")
        raise

def init_assets():
    """Initialize the database with workout assets."""
    db = next(database.get_db())
    try:
        load_assets(db)
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_assets()
