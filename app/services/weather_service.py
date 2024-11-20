import requests
import os
from app.models import User, SubscriptionContent
import logging
from sqlalchemy import func
from datetime import datetime
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app import db
import pytz

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

def fetch_weather(location, units="metric"): # I dont think units work in this api call request? 
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



def fetch_and_save_weather(location, units="metric"):
    """
    Fetches weather data for a location and saves the result to the SubscriptionContent model.

    Args:
        location (str): The location for which to fetch weather.
        units (str): Units for temperature ('metric', 'imperial', or default). Default is 'metric'.

    Returns:
        tuple: The response from the weather API and a success/error message.
    """
    # Fetch weather data from OpenWeatherMap API
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units={units}'
    try:
        logger.info(f"Fetching weather data for location: {location}")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response code is not 200
        
        # Get the JSON data from the response
        weather_data = response.json()
        logger.info(f"Weather data fetched successfully for {location}")

        # Save the data to the SubscriptionContent model
        new_subscription_content = SubscriptionContent(
            subscription_type="WeatherUpdateNow",  # Example subscription type
            result=weather_data
        )
        
        # Add to the session and commit to save
        db.session.add(new_subscription_content)
        db.session.commit()
        logger.info("Weather data saved successfully to the database")

        return weather_data, None  # Return the weather data and no error message
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while fetching weather data for {location}: {str(e)}")
        return None, f"Request error: {str(e)}"
    
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback in case of database errors
        logger.error(f"Database error while saving weather data for {location}: {str(e)}")
        return None, f"Database error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error while processing weather data for {location}: {str(e)}")
        return None, f"Unexpected error: {str(e)}"




# Function to format weather data
def get_formatted_weather(location, units="metric"):
    """
    Formats the weather data for a given location into a readable string.
    
    Args:
        location (str): Name of the city/location.
        units (str): Units for temperature. Default is "metric".
        
    Returns:
        str: A formatted string containing weather information.
        str: An error message if the formatting or data retrieval fails.
    """
    try:
        # Call the fetch_weather function to get raw weather data
        data, error = fetch_weather(location, units)

        if error:
            return None, error

        # Extract relevant weather details
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        # Determine the temperature unit (°C or °F)
        temp_unit = "°F" if units == "imperial" else "°C"

        # Format the data into a string
        weather_string = (f"The current weather in {location} is: {weather}. "
                          f"The temperature is {temperature}{temp_unit} with a humidity of {humidity}%. "
                          f"Wind speed is {wind_speed} m/s.")
        return weather_string, None

    except Exception as e:
        return None, str(e)


from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import cast, Date
from sqlalchemy import String


from datetime import datetime, timezone

def fetch_weather_from_db(location):
    """
    Fetch weather data from the database for a specific location.

    Args:
        location (str): The location to filter weather data.

    Returns:
        tuple: (weather_data (dict), error_message (str))
    """
    try:
        # Get today's date in UTC
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        today = utc_now.date()
        print("db comparing to location :", location)

        # Query the database for weather data
        weather_data = SubscriptionContent.query.filter(
            SubscriptionContent.subscription_type == 'WeatherUpdateNow',
            #cast(SubscriptionContent.result["name"], String) == location  # Cast JSON field to String
            cast(SubscriptionContent.fetch_date, Date) == today           # Compare date
        ).order_by(SubscriptionContent.fetch_date.desc()).first()

        if weather_data:
            logger.info("Weather data result from db: %s", weather_data.result)
            return weather_data.result, None
        
        return None, "No matching weather data found in the database."
    
    except Exception as e:
        logger.error("Error fetching weather data: %s", str(e))
        return None, f"Error fetching weather data: {str(e)}"


from sqlalchemy import text

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
            # The `result` is a RowProxy object, parse accordingly
            logger.info("Weather data result from DB: %s", result)
            return result, None
        else:
            return None, "No matching weather data found in the database."
    except Exception as e:
        logger.exception("Error fetching weather data using raw SQL: %s", str(e))
        return None, f"Error fetching weather data: {str(e)}"


def format_HTML_weather_container(weather_data):
    """
    Formats weather results into an HTML container.

    Args:
        weather_data (dict): Dictionary containing weather results.

    Returns:
        str: HTML formatted weather data.
    """
    try:
        # Extract weather data based on the correct structure
        location = weather_data.get("name", "Unknown Location")
        temperature = weather_data["main"].get("temp", "N/A")  # Extract temp from the 'main' field
        condition = weather_data["weather"][0].get("description", "N/A")  # Extract description from 'weather' list
        
        # Create the HTML content for the weather update
        html = f"""
        <div>
            <h2>Weather Update</h2>
            <p><strong>Location:</strong> {location}</p>
            <p><strong>Temperature:</strong> {temperature}°F</p>
            <p><strong>Condition:</strong> {condition}</p>
        </div>
        """
        return html
    except Exception as e:
        logger.error("Error formatting weather container: %s", str(e))
        return "<div>Error formatting weather data.</div>"

