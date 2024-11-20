from flask_mail import Message
from app import mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.weather_service import format_HTML_weather_container
from app.services.news_service import format_HTML_news_container
import logging


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def email_engine(user_subscription_results):
    """
    Routes the subscription data to functions that return HTML formatted data.

    Args:
        user_subscription_results (dict): A dictionary containing the queried results and/or fetched results.

    Returns:
        dict: A dictionary containing the HTML formatted containers for each subscription.
    """
    logger.info("Started email engine.")
    formatted_results = {}
    logger.debug("Raw subscription data received: %s", user_subscription_results)

    for key, data in user_subscription_results.items():
        if key == 'weather':
            formatted_results[key] = format_HTML_weather_container(data)
        elif key == 'news':
            logger.debug("Raw news data received: %s", data)
            formatted_results[key] = format_HTML_news_container(data)
        else:
            logger.warning("Unknown subscription type: %s", key)

    logger.info("Email engine successfully formatted results.")
    return formatted_results

        
def add_email_headers(html_formatted_user_subscription_results):
    """
    Extracts each HTML subscription container from the dict and adds email header and footer.

    Args:
        html_formatted_user_subscription_results (dict): A dictionary containing the HTML formatted containers for each subscription.

    Returns:
        dict: A dictionary containing the HTML formatted email body with proper headers.
    """
    email_with_headers = {}

    header = "<html><body><h1>Your Daily Updates</h1><hr>"
    footer = "<hr><p>Thank you for subscribing!</p></body></html>"

    for key, content in html_formatted_user_subscription_results.items():
        email_with_headers[key] = f"{header}{content}{footer}"

    logger.info("Added headers and footers to email content.")
    return email_with_headers


def send_email(to, subject, html_content):
    try:
        msg = Message(subject, recipients=[to])
        msg.html = html_content
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)