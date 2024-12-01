import os
import json
from sqlalchemy.orm import Session
from . import models, database
import logging
import re

logger = logging.getLogger(__name__)

def clean_html_content(content):
    """Clean HTML content to extract plain text with minimal formatting."""
    if not content:
        return ""
    # Remove HTML classes and other attributes
    content = re.sub(r'class="[^"]*"', '', content)
    content = re.sub(r'data-[^=]*="[^"]*"', '', content)
    
    # Convert specific HTML elements to plain text or minimal markdown
    content = content.replace('<p>', '').replace('</p>', '\n')
    content = content.replace('<ul>', '\n').replace('</ul>', '\n')
    content = content.replace('<li>', '• ').replace('</li>', '\n')
    content = content.replace('<ol>', '\n').replace('</ol>', '\n')
    content = content.replace('<col>', '').replace('</col>', '')
    content = content.replace('<div>', '').replace('</div>', '\n')
    
    # Clean up multiple newlines and spaces
    content = re.sub(r'\n\s*\n', '\n', content)
    content = re.sub(r' +', ' ', content)
    return content.strip()

def extract_content_by_title(content_data, title):
    """Extract specific content section by title from the content array."""
    for item in content_data.get('content', []):
        if item.get('type') == 'section' and item.get('title') == title:
            content = item.get('content', '')
            return clean_html_content(content)
    return ''

def extract_image_paths(content_data, exercise_path):
    """Extract image and animation paths from content array."""
    image_path = None
    animation_path = None
    
    # First try to find images in the exercise directory
    exercise_files = os.listdir(exercise_path)
    for file in exercise_files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Create relative path from exercise directory
            rel_path = os.path.join('exercises',
                                  os.path.basename(os.path.dirname(exercise_path)),
                                  os.path.basename(exercise_path),
                                  file).replace('\\', '/')
            image_path = rel_path
            break
        elif file.lower().endswith('.gif'):
            rel_path = os.path.join('exercises',
                                  os.path.basename(os.path.dirname(exercise_path)),
                                  os.path.basename(exercise_path),
                                  file).replace('\\', '/')
            animation_path = rel_path
    
    return image_path, animation_path

def load_assets(db: Session):
    """
    Load workout assets from the Fitness Assets directory into the database.
    """
    assets_dir = os.path.join(os.path.dirname(__file__), "Fitness_Assets")
    logger.info(f"Loading assets from: {assets_dir}")
    
    if not os.path.exists(assets_dir):
        error_msg = f"Error: Assets directory not found at {assets_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Clear existing assets
    try:
        db.query(models.WorkoutAsset).delete()
        db.commit()
        logger.info("Cleared existing workout assets")
    except Exception as e:
        logger.error(f"Error clearing existing assets: {str(e)}")
        db.rollback()
        raise
    
    # Process each category
    for category in os.listdir(assets_dir):
        category_path = os.path.join(assets_dir, category)
        if not os.path.isdir(category_path):
            continue
            
        category_name = category.replace("_Exercises", "").strip()
        logger.info(f"Processing category: {category_name}")
        
        # Create a workout asset for each exercise
        for exercise_name in os.listdir(category_path):
            exercise_path = os.path.join(category_path, exercise_name)
            if not os.path.isdir(exercise_path):
                continue
                
            # Read content.json
            content_file = os.path.join(exercise_path, "content.json")
            if not os.path.exists(content_file):
                logger.warning(f"No content.json found for {exercise_name}")
                continue
                
            logger.info(f"Processing exercise: {exercise_name}")
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                
                # Extract content sections
                title = content_data.get('title', exercise_name)
                instructions = extract_content_by_title(content_data, f"{title} Instructions")
                benefits = extract_content_by_title(content_data, f"{title} Benefits")
                muscles = extract_content_by_title(content_data, f"{title} Muscles Worked")
                variations = extract_content_by_title(content_data, f"{title} Variations & Alternatives")
                description = extract_content_by_title(content_data, f"{title} Form & Visual")
                
                # Extract image paths
                image_path, animation_path = extract_image_paths(content_data, exercise_path)
                
                # Create workout asset
                workout_asset = models.WorkoutAsset(
                    title=title,
                    description=description,
                    category=category_name,
                    difficulty="Intermediate",  # Default difficulty
                    instructions=instructions,
                    benefits=benefits,
                    muscles_worked=muscles,
                    variations=variations,
                    image_path=image_path,
                    animation_path=animation_path
                )
                
                db.add(workout_asset)
                db.commit()
                logger.info(f"Added exercise: {workout_asset.title}")
                
            except Exception as e:
                logger.error(f"Error processing {exercise_name}: {str(e)}")
                db.rollback()
                continue
    
    logger.info("Finished loading assets")

def init_assets():
    """Initialize the database with workout assets."""
    db = next(database.get_db())
    try:
        load_assets(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_assets()
