from flask import Blueprint, jsonify, render_template
from app.services.email_service import send_email, add_email_headers, email_engine
from app.services.user_service import get_all_users
from app.services.weather_service import fetch_and_save_weather
from app.services.news_service import fetch_news, fetch_source_ids
from app.services.main_service import subscription_router
from app.models import User
import logging
from app import db
import os 

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/send', methods=['POST'])
@main_bp.route('/')
def index():
    logger.info("Rendering index page")
    return render_template('index.html')


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

        # Call email_engine to format the content and prepare HTML email
        formatted_content = email_engine(content)
        logger.debug("Formatted content: %s", formatted_content)

        # Combine all subscription content into a single email body
        html_body = "".join(html_content for html_content in formatted_content.values())
        html_with_headers = add_email_headers({"all": html_body})["all"]  # Add headers and footers
        
        # Send the email
        success, message = send_email(user.email, "Daily Newsletter", html_with_headers)

        if not success:
            logger.error("Failed to send email: %s", message)
            return jsonify({"error": message}), 500

        logger.info("Newsletter sent to user: %s", user.email)
        return jsonify({"message": "Newsletter sent to first user successfully"}), 200

    except Exception as e:
        logger.exception("An error occurred while sending newsletter: %s", str(e))
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
