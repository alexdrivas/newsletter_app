import requests
from dotenv import load_dotenv
import os

load_dotenv()

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

def fetch_weather(location, units="metric"): # I dont think units work in this api call request? 
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units={units}'
    try:
        response = requests.get(url)
        response.raise_for_status()
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
