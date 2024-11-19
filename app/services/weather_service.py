import requests
import os
from app.models import User, SubscriptionContent
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

def fetch_weather(location, units="metric"): # I dont think units work in this api call request? 
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units={units}'
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Save the resp into the Sbscription Content Dict. 
        return response.json(), None
    except requests.exceptions.RequestException as e:
        return None, f"Error: {str(e)}"


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



def fetch_weather_from_db(location, units):
    """
    Fetch weather data from the database where the given location and units are present
    anywhere in the nested result JSON.

    Args:
        location (str): Location for which weather data is required.
        units (str): Units of measurement (e.g., 'metric').

    Returns:
        tuple: (weather_data (dict), error_message (str))
    """
    try:
        # Query the database to check if both location and units are in the JSON result
        weather_data = SubscriptionContent.query.filter(
            SubscriptionContent.subscription_type == 'WeatherUpdateNow',
            # Use JSONB functions to search within JSON field
            SubscriptionContent.result.like(f'%\"location\": \"{location}\"%'),
            SubscriptionContent.result.like(f'%\"units\": \"{units}\"%')
        ).order_by(SubscriptionContent.fetch_date.desc()).first()

        if weather_data:
            return weather_data.result, None
        else:
            return None, "No matching weather data found in the database."
    except Exception as e:
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
            <p><strong>Temperature:</strong> {temperature}°</p>
            <p><strong>Condition:</strong> {condition}</p>
        </div>
        """
        return html
    except Exception as e:
        logger.error("Error formatting weather container: %s", str(e))
        return "<div>Error formatting weather data.</div>"

