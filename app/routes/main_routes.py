from flask import Blueprint, jsonify, render_template
from app.services.email_service import send_email
from app.services.user_service import get_all_users
from app.services.weather_service import get_formatted_weather
from app.models import User
import logging
from app import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/send', methods=['POST'])
@main_bp.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')

# Centralized router function that dynamically routes based on subscription
def subscription_router(user_subscriptions):
    """
    Routes the subscriptions to relevant API functions and sends the API response.

    Args:
        user_subscriptions (list): List of user's subscriptions.
        
    Returns:
        dict: A dictionary containing the combined results from all APIs.
    """
    logger.info("Started subscription router with %d subscriptions", len(user_subscriptions))
    results = {}

    for sub in user_subscriptions:
        if sub['name'] == 'WeatherUpdateNow':
            # Parse the details from the subscription
            location = sub['details'].get('location')
            units = sub['details'].get('units', 'metric')  # Default to 'metric' if not provided
            frequency = sub['details'].get('frequency', 'daily')  # Frequency (not used yet, but could be useful)

            logger.debug("Fetching weather for location: %s, units: %s", location, units)

            # Call the function for weather update
            weather_content, weather_error = get_formatted_weather(location, units)
            if weather_error:
                results['weather'] = f"Failed to fetch weather: {weather_error}"
                logger.error("Weather fetch failed: %s", weather_error)
            else:
                results['weather'] = weather_content
                logger.info("Weather fetched successfully: %s", weather_content)
            
        # Add other subscription handling here (for News, Stocks, etc.)

    return results

@main_bp.route('/send_newsletter_to_user', methods=['POST'])
def send_newsletter_to_user():
    try:
        logger.info("Attempting to retrieve users")
        user = get_all_users()
        if not user:  # Check if get_all_users returned None
            logger.warning("No users found in the database")
            return jsonify({"error": "No users found"}), 404

        logger.info("User selected: %s", user)

        # Parse subscriptions
        user_subscriptions = user.subscriptions.get('subscriptions', [])
        if not isinstance(user_subscriptions, list):
            logger.error("Invalid subscriptions format: Expected a list but got %s", type(user_subscriptions))
            return jsonify({"error": "Invalid subscriptions format"}), 400
        
        logger.debug("User subscriptions: %s", user_subscriptions)

        # Call the subscription router to process subscriptions
        content = subscription_router(user_subscriptions)
        logger.debug("Generated content: %s", content)
        
        if not content:
            logger.warning("No content generated for newsletter")
            return jsonify({"error": "No content generated"}), 500

        # Prepare the email content
        content_text = "\n".join(f"{key}: {value}" for key, value in content.items())
        logger.debug("Prepared email content: %s", content_text)

        # Send the email
        success, message = send_email(user.email, "Daily Newsletter", content_text)
        if not success:
            logger.error("Failed to send email: %s", message)
            return jsonify({"error": message}), 500

        logger.info("Newsletter sent to user: %s", user.email)
        return jsonify({"message": "Newsletter sent to first user successfully"}), 200

    except Exception as e:
        logger.exception("An error occurred while sending newsletter: %s", str(e))
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
