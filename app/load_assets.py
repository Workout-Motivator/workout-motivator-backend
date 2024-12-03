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

            # Create workout asset
            workout_asset = models.WorkoutAsset(
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

            db.add(workout_asset)
            logger.info(f"Added exercise: {workout_asset.title}")

        except Exception as e:
            logger.error(f"Error processing {exercise_dir}: {str(e)}")

def load_assets(db: Session):
    """Load all fitness assets into the database."""
    try:
        logger.info("Starting asset loading process...")
        
        # Clear existing assets
        existing_count = db.query(models.WorkoutAsset).count()
        logger.info(f"Found {existing_count} existing assets")
        db.query(models.WorkoutAsset).delete()
        db.commit()
        logger.info("Cleared existing assets")

        # Get the absolute path to the assets directory
        current_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(current_dir, "app", "assets")
        
        if not os.path.exists(assets_dir):
            raise FileNotFoundError(f"Assets directory not found: {assets_dir}")
        
        # Get all exercise categories
        categories = [d for d in os.listdir(assets_dir) 
                     if os.path.isdir(os.path.join(assets_dir, d)) and "Exercises" in d]
        
        total_assets = 0
        for category in categories:
            category_dir = os.path.join(assets_dir, category)
            exercises = [d for d in os.listdir(category_dir) 
                        if os.path.isdir(os.path.join(category_dir, d))]
            
            for exercise in exercises:
                try:
                    exercise_dir = os.path.join(category_dir, exercise)
                    content_file = os.path.join(exercise_dir, "content.json")
                    
                    if not os.path.exists(content_file):
                        logger.warning(f"No content.json found for {exercise}")
                        continue
                        
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                    
                    # Extract exercise data
                    asset_data = {
                        "title": content_data.get("title", exercise),
                        "category": category.replace("_Exercises", "").strip(),
                        "description": "",
                        "instructions": "",
                        "benefits": "",
                        "muscles_worked": "",
                        "image_path": ""
                    }
                    
                    # Process content sections
                    for section in content_data.get("content", []):
                        if section["type"] == "image" and not asset_data["image_path"]:
                            # Extract image filename from path and check if it exists in exercise dir
                            image_name = os.path.basename(section["path"].replace("images/", ""))
                            image_path = os.path.join(exercise_dir, image_name)
                            if os.path.exists(image_path):
                                # Store relative path from assets directory
                                rel_path = os.path.relpath(image_path, assets_dir)
                                asset_data["image_path"] = rel_path.replace("\\", "/")
                                logger.info(f"Found image: {asset_data['image_path']}")
                        
                        elif section["type"] == "section":
                            section_title = section.get("title", "").lower()
                            section_content = section.get("content", {})
                            
                            if "instruction" in section_title:
                                if isinstance(section_content, dict) and "items" in section_content:
                                    asset_data["instructions"] = "\n".join(section_content["items"])
                            elif "benefit" in section_title:
                                if isinstance(section_content, dict) and "items" in section_content:
                                    asset_data["benefits"] = "\n".join(section_content["items"])
                            elif "muscles" in section_title:
                                if isinstance(section_content, dict) and "items" in section_content:
                                    asset_data["muscles_worked"] = ", ".join(section_content["items"])
                            elif section_content and isinstance(section_content, str):
                                # Use section content as description if it's a string
                                asset_data["description"] = section_content
                    
                    # Create database entry
                    db_asset = models.WorkoutAsset(**asset_data)
                    db.add(db_asset)
                    db.commit()
                    total_assets += 1
                    logger.info(f"Added asset to database: {asset_data['title']} ({asset_data['category']})")
                    
                except Exception as exercise_error:
                    logger.error(f"Error processing exercise {exercise}: {str(exercise_error)}")
                    continue
        
        logger.info(f"Successfully loaded {total_assets} assets")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading assets: {str(e)}")
        raise e

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
