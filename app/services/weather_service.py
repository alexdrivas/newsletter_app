import requests
import os
from app.models import User, SubscriptionContent
import logging
#from sqlalchemy import func
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app import db
import pytz
from sqlalchemy import text
#from sqlalchemy.dialects.postgresql import JSONB
#from sqlalchemy import cast, Date
#from sqlalchemy import String

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

def fetch_and_save_weather(location, units="metric"): # I dont think units work in this api call request? 
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units={units}'
    try:
        response = requests.get(url)
        response.raise_for_status()

        response = response.json()
        logger.info("Response going into save weathe data: ", response)

        # Save weather data to Subscription Content table
        save_weather_data(response)

        # Save the resp into the Sbscription Content Dict. 
        return response, None
    except requests.exceptions.RequestException as e:
        return None, f"Error: {str(e)}"

# Assuming SubscriptionContent and db are already imported
def save_weather_data(weather_data):
    try:
        # Create a new SubscriptionContent entry without providing the 'id' field
        new_subscription_content = SubscriptionContent(
            subscription_type="WeatherUpdateNow",  # Example subscription type
            result=weather_data,  # Weather data from the API response
            fetch_date=datetime.utcnow()  # Current UTC time
        )
        
        # Add to the session and commit the transaction to save it in the database
        db.session.add(new_subscription_content)
        db.session.commit()
        logging.info("Weather data saved successfully")

    except SQLAlchemyError as e:
        # Handle any SQLAlchemy errors (like unique constraint violations)
        db.session.rollback()  # Rollback the transaction if error occurs
        logging.error(f"Weather fetch failed: Database error: {str(e)}")
        return None, f"Database error: {str(e)}"

    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"Unexpected error occurred while saving weather data: {str(e)}")
        return None, f"Error: {str(e)}"

    return new_subscription_content, None  # Return the saved record and no error

from sqlalchemy.sql import text
from datetime import datetime

def fetch_weather_from_db_raw(location):
    """
    Fetch weather data using a raw SQL query.
    """
    try:
        # Get today's date in UTC
        utc_now = datetime.utcnow().date()

        # Raw SQL query
        query = text("""
            SELECT *
            FROM subscription_content
            WHERE subscription_type = :subscription_type
              AND result->>'name' = :location
              AND fetch_date >= :fetch_date
            ORDER BY fetch_date DESC
            LIMIT 1;
        """)

        # Execute the query with bound parameters
        result = db.session.execute(query, {
            'subscription_type': 'WeatherUpdateNow',
            'location': location,
            'fetch_date': utc_now
        }).fetchone()

        if result:
            # Safely convert Row to a dictionary
            result_dict = dict(result._mapping)
            logger.info("Weather data result from DB: %s", result_dict)
            result_dict = result_dict['result']
            logger.info("Weather data after indexed: %s", result_dict)
            return result_dict, None
        else:
            return None, "No matching weather data found in the database."
    except Exception as e:
        logger.exception("Error fetching weather data using raw SQL: %s", str(e))
        return None, f"Error fetching weather data: {str(e)}"


def format_HTML_weather_container(weather_data):
    """
    Formats weather results into a minimal and clean HTML container, inspired by James Clear's newsletter style.

    Args:
        weather_data (dict): Dictionary containing weather results.

    Returns:
        str: HTML formatted weather data.
    """
    try:
        logger.info("Formatting weather data: %s", weather_data)
        
        # Extract weather data
        location = weather_data.get("name", "Unknown Location")
        temperature = round_temperature(weather_data["main"].get("temp", "N/A"))  # Round temp
        temp_min = round_temperature(weather_data["main"].get("temp_min", "N/A"))  # Round temp_min
        temp_max = round_temperature(weather_data["main"].get("temp_max", "N/A"))  # Round temp_max
        condition = weather_data["weather"][0].get("description", "N/A").capitalize()  # Capitalize condition
        
        # Get current date and day of the week
        today = datetime.today()
        day_of_week = today.strftime("%A")
        current_date = today.strftime("%d %b %Y")
        
        # Define a placeholder icon
        weather_icon = get_weather_icon(condition)
        
        # Create the HTML content for the weather update
        html = f"""
            <div style="font-family: 'Quicksands', sans-serif; color: #333333; padding: 20px; background-color: #FFFFFF; border-radius: 8px; max-width: 600px; margin: 20px auto; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">

                <!-- Header -->
                <div style="text-align: left; margin-bottom: 20px; border-bottom: 1px solid #EAEAEA; padding-bottom: 10px;">
                    <h1 style="font-size: 20px; margin: 5px 0; color: #222;">Latest Weather</h1>
                </div>
                
                <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #CFA488; border-radius: 8px; background-color: #FFFFFF;">
                    <!-- Date -->
                    <div style="text-align: left; margin-bottom: 15px;">
                        <h3 style="font-size: 16px; margin: 5px 0; color: #777;">{day_of_week}</h3>
                        <p style="font-size: 12px; margin: 0; color: #777;">{current_date}</p>
                        <p style="font-size: 12px; margin: 0; color: #777;">{location}, {weather_data.get('sys', {}).get('country', '')}</p>
                    </div>
                    
                    <!-- Weather Icon and Temperature in Columns -->
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <!-- Weather Icon -->
                        <div style="flex: 1; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 5px; color: #CFA488;">{weather_icon}</div>
                        </div>
                        
                        <!-- Temperature -->
                        <div style="flex: 2; text-align: center;">
                            <p style="font-size: 48px; margin: 0; color: #222;">{temperature}°F</p>
                            <p style="font-size: 16px; margin: 5px 0; color: #666;">{condition}</p>
                        </div>
                    </div>
                    
                    <!-- High/Low Temperatures -->
                    <div style="display: flex; justify-content: space-evenly; align-items: center; font-size: 14px; color: #555;">
                        <div style="text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #CFA488;">&#x25B2; {temp_max}°F</p>
                        </div>
                        <div style="text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #87AFC7;">&#x25BC; {temp_min}°F</p>
                        </div>
                    </div>
                </div>
            </div>
            """

        return html
    except Exception as e:
        logger.error("Error formatting weather container: %s", str(e))
        return "<div>Error formatting weather data.</div>"

def round_temperature(value):
    """
    Rounds the temperature value to the nearest whole number.

    Args:
        value (float): The temperature value.

    Returns:
        int or str: The rounded temperature value as an integer, or 'N/A' if the input is invalid.
    """
    try:
        return round(float(value))
    except (ValueError, TypeError):
        return "N/A"
    

def get_weather_icon(description):
    """
    Returns an emoji representing the weather based on the description.
    
    :param description: str, a brief weather description (e.g., 'clear sky', 'light rain')
    :return: str, an emoji representing the weather
    """
    description = description.lower()  # Normalize to lowercase for matching
    
    # Mapping descriptions to icons
    if "clear" in description:
        if "night" in description:
            return "🌙"  # Night icon
        return "☀️"  # Sun icon
    elif "cloud" in description or "clouds" in description:
        return "☁️"  # Cloud icon
    elif "rain" in description or "shower" in description:
        return "🌧️"  # Rain icon
    elif "snow" in description:
        return "❄️"  # Snow icon
    elif "thunder" in description or "storm" in description:
        return "🌩️"  # Thunderstorm icon
    elif "mist" in description or "fog" in description or "haze" in description:
        return "🌫️"  # Mist/Fog icon
    elif "drizzle" in description:
        return "🌦️"  # Drizzle icon
    else:
        return "❓"  # Unknown/Default icon
    



        html = f"""
        <div style="font-family: 'Quicksands', sans-serif; color: #333; padding: 10px; background-color: #FFF; border-radius: 8px; max-width: 600px; margin: 10px auto; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">

                <!-- First Column: Large Temperature -->
                <div style="flex: 0 0 25%; text-align: center;">
                    <p style="font-size: 40px; font-weight: bold; color: #CFA488; margin: 5px 0;">{temperature}°F</p>
                </div>
                
                <!-- Second Column: Icon and Min/Max Temps -->
                <div style="flex: 0 0 15%; text-align: center;">
                    <!-- Weather Icon -->
                    <div style="font-size: 30px; color: #CFA488; margin-bottom: 5px;">{weather_icon}</div>
                    <!-- Min/Max Temps -->
                    <div style="font-size: 12px; color: #555;">
                        <p style="margin: 0; color: #CFA488;">&#x25B2; {temp_max}°F</p>
                        <p style="margin: 0; color: #87AFC7;">&#x25BC; {temp_min}°F</p>
                    </div>
                </div>
                
                <!-- Third Column: Date and Location -->
                <div style="flex: 0 0 60%; padding-left: 10px; display: flex; flex-direction: column; justify-content: space-between;">
                    <!-- Location and Country -->
                    <div style="font-size: 12px; text-align: left; color: #555;">
                        <p style="margin: 2px 0;">{location}, {weather_data.get('sys', {}).get('country', '')}</p>
                    </div>
                    <!-- Date -->
                    <div style="font-size: 12px; text-align: left; color: #555;">
                        <p style="margin: 2px 0;">{day_of_week}</p>
                        <p style="margin: 2px 0;">{current_date}</p>
                    </div>
                    <!-- Condition -->
                    <div style="font-size: 12px; text-align: right; color: rgba(102, 102, 102, 0.8); margin-top: auto;">
                        <p style="margin: 2px 0; font-style: italic;">{condition}</p>
                    </div>
                </div>
            </div>
        </div>
        """