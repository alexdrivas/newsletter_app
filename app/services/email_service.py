from flask_mail import Message
from app import mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.weather_service import format_HTML_weather_container
from app.services.news_service import format_HTML_news_container, normalize_news_data
import logging
#from sqlalchemy.engine.row import Row

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
            # Process weather data directly as a dictionary
            if isinstance(data, dict):
                logger.debug("Processing weather data: %s", data)
                try:
                    formatted_results[key] = format_HTML_weather_container(data)
                except Exception as e:
                    logger.error("Error formatting weather container: %s", e)
                    formatted_results[key] = "<div>Error formatting weather data.</div>"
            else:
                logger.warning("Unexpected data type for weather: %s", type(data))
                formatted_results[key] = "<div>Invalid weather data format.</div>"
        elif key == 'news':
            logger.debug("Raw news data received: %s", data)
            try:
                normalized_news_data = normalize_news_data(data)
                formatted_results[key] = format_HTML_news_container(normalized_news_data)
            except Exception as e:
                logger.error("Error formatting news container: %s", e)
                formatted_results[key] = "<div>Error formatting news data.</div>"
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


    # Header inspired by James Clear's design
    header = """
    <html>
        <head>
            <style>
                body {
                    font-family: 'Tahoma', sans-serif;
                    color: #333333;
                    background-color: #FAFAFA;
                    margin: 0;
                    padding: 0;
                }
                .header-container {
                    text-align: center;
                    background-color: #F9F7F5;
                    padding: 30px 0;
                    border-bottom: 1px solid #EAEAEA;
                }
                .header-title {
                    font-size: 24px;
                    font-weight: bold;
                    margin: 0;
                    color: #222222;
                }
                .header-subtitle {
                    font-size: 14px;
                    color: #666666;
                    margin: 5px 0 0;
                }
                .content-container {
                    background-color: #FFFFFF;
                    margin: 20px auto;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    font-family: 'Tahoma', sans-serif;
                }
                h1 {
                    font-size: 22px;
                    font-weight: bold;
                    margin-top: 0;
                    color: #222222;
                }
                p {
                    font-size: 16px;
                    line-height: 1.6;
                    color: #555555;
                }
                .footer {
                    text-align: center;
                    padding: 20px 0;
                    color: #999999;
                    font-size: 12px;
                }
                .footer a {
                    color: #888888;
                    text-decoration: none;
                }
                .footer a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="header-container">
                <h1 class="header-title">Today's Newsletter</h1>
                <p class="header-subtitle">"Content delivered, daily."</p>
            </div>
    """
    
    # Footer
    footer = """
            <div class="footer">
                <p>You're receiving this email because you subscribed to our newsletter.</p>
                <p>
                    <a href="#">Unsubscribe</a> | 
                    <a href="#">Manage Preferences</a>
                </p>
            </div>
        </body>
    </html>
    """

    # Adding headers and footers to the content
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