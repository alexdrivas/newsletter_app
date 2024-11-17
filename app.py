from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import relationship
from flask_mail import Mail, Message
from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid
import json
import os
import requests
import logging


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
app.config['MAIL_DEFAULT_SENDER'] = 'aadrivas@gmail.com'
mail = Mail(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://alexandrosdrivas@localhost/alexandrosdrivas'
# Get your OpenWeather API key from the environment
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

logging.basicConfig(level=logging.DEBUG)



#Constants 
WEATHERUPDATENOW = "weather_update_now"


print("Connecting to the database...")
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
print("Connected to the database.")

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscriptions = db.Column(JSONB, nullable=False, default={})

    def __init__(self, first_name, last_name, email, subscriptions=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.subscriptions = subscriptions or {}

    def __repr__(self):
        return f"<User {self.email}>"

# CachedContent Model
class CachedContent(db.Model):
    __tablename__ = 'cached_content'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subscription_type = db.Column(db.String(100), nullable=False)
    arguments = db.Column(JSONB, nullable=False)
    data = db.Column(JSONB, nullable=False)
    cached_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=True)

    def __init__(self, subscription_type, arguments, data, expiration_date=None):
        self.subscription_type = subscription_type
        self.arguments = arguments
        self.data = data
        self.expiration_date = expiration_date

    def __repr__(self):
        return f"<CachedContent {self.subscription_type} at {self.cached_at}>"

@app.route('/')
def index():
    return render_template('index.html')

def insert_user(first_name, last_name, email):
    # Create a new User instance
    new_user = User(first_name=first_name, last_name=last_name, email=email)
    # Add the new user to the session
    db.session.add(new_user)
    # Commit the session to persist changes to the database
    db.session.commit()

# Usage:
@app.route('/create_user', methods=['POST'])
def create_user():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    
    # Call the insert_user function to insert the user into the database
    insert_user(first_name, last_name, email)

    return redirect(url_for('index'))

def get_all_users():
    return User.query.first()  # Retrieve the first user



# Subscription Function for WeatherUpdateNow
def weather_update_now(location, units="metric"):
    """
    Fetches raw weather data from OpenWeatherMap API for a given location.
    
    Args:
        location (str): Name of the city/location.
        units (str): Units for temperature. Default is "metric".
        
    Returns:
        dict: The JSON response from the API if successful.
        str: An error message if the API call fails.
    """
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units={units}'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
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
        # Call the first function to get raw weather data
        data, error = weather_update_now(location, units)

        if error:
            return None, error

        # Extract relevant weather details
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        # Format the data into a string
        weather_string = (f"The current weather in {location} is: {weather}. "
                          f"The temperature is {temperature}°C with a humidity of {humidity}%. "
                          f"Wind speed is {wind_speed} m/s.")
        return weather_string, None

    except Exception as e:
        return None, str(e)

# Centralized router function that dynamically routes based on subscription
def subscription_router(user_subscriptions):
    """
    Routes the subscriptions to relevant API functions and sends the API response.

    Args:
        user_subscriptions (list): List of user's subscriptions.
        
    Returns:
        dict: A dictionary containing the combined results from all APIs.
    """
    results = {}

    for sub in user_subscriptions:
        if sub['name'] == 'WeatherUpdateNow':
            # Parse the details from the subscription
            location = sub['details'].get('location')
            units = sub['details'].get('units', 'metric')  # Default to 'metric' if not provided
            frequency = sub['details'].get('frequency', 'daily')  # Frequency (not used yet, but could be useful)

            # Call the function for weather update
            weather_content, weather_error = get_formatted_weather(location, units)
            if weather_error:
                results['weather'] = f"Failed to fetch weather: {weather_error}"
            else:
                results['weather'] = weather_content
            
        # Add other subscription handling here (for News, Stocks, etc.)

    return results

@app.route('/send_newsletter_to_user', methods=['POST'])
def send_newsletter_to_user():
    try:
        user = get_all_users()
        if not user:  # Check if get_all_users returned None
            return jsonify({"error": "No users found"}), 404

        # Parse subscriptions
        user_subscriptions = user.subscriptions.get('subscriptions', [])
        if not isinstance(user_subscriptions, list):
            return jsonify({"error": "Invalid subscriptions format"}), 400

        # Call the subscription router to process subscriptions
        content = subscription_router(user_subscriptions)
        
        if not content:
            return jsonify({"error": "No content generated"}), 500

        # Prepare the email content
        content_text = "\n".join(f"{key}: {value}" for key, value in content.items())
        print("content_text", content_text)

        # Send the email
        success, message = send_email(user.email, "Daily Newsletter", content_text)
        if not success:
            return jsonify({"error": message}), 500

        return jsonify({"message": "Newsletter sent to first user successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Email sender function
def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    app.run(debug=True)
