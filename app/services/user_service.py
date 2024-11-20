from app.models import User  # Ensure User is imported correctly
import logging
from app import db
from sqlalchemy import text

# Configure logging
logger = logging.getLogger(__name__)

def get_all_users():
    logger.info("Attempting to retrieve the first user from the database")

    try:
        # Test the database connection
        logger.debug("Testing database connection...")
        result = db.session.execute(text('SELECT 1'))  # Simple query to check DB connection
        logger.debug("Database connection successful: %s", result)

        user = User.query.get(1)  # Retrieve the first user
        if user:
            logger.info("Successfully retrieved user: %s", user)
        else:
            logger.warning("No user found in the database")
        
        return user

    except Exception as e:
        logger.error("Error fetching user: %s", e)
        return None
