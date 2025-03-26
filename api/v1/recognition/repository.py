# backend/app/recognition/repository.py

from sqlalchemy.orm import Session

def save_image_metadata(filename: str, result: str, db: Session):
    """
    Save metadata about the uploaded image and the result into the database.
    Here we simply store the filename and processing result.
    """
    try:
        image_data = {
            "filename": filename,
            "result": result
        }
        db.add(image_data)  # Assuming SQLAlchemy ORM is used for simplicity
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving image metadata: {e}")
