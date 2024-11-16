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
 


# Helper: Fetch formatted weather data
def get_formatted_weather(location):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric'

    try:
        response = requests.get(url)
        data = response.json()

        if data.get('cod') != 200:
            return None, f"Error: {data.get('message', 'Unknown error')}"

        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        weather_string = (f"The current weather in {location} is: {weather}. "
                          f"The temperature is {temperature}°C with a humidity of {humidity}%. "
                          f"Wind speed is {wind_speed} m/s.")
        return weather_string, None

    except Exception as e:
        return None, str(e)


# Email sender function
def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)


@app.route('/send_email_to_first_user', methods=['POST'])
def send_email_to_first_user():

    try:
        location = 'San Francisco'  # Default location

        weather_content, weather_error = get_formatted_weather(location)
        if not weather_content: print("No weather content")

        if weather_error:
            return jsonify({"error": f"Failed to fetch weather: {weather_error}"}), 500

        content_text = weather_content  # Combine database content and weather
        print("content_text", content_text)

        user = User.query.first()
        if not user:
            return jsonify({"error": "No users found"}), 404

        success, message = send_email(user.email, "Daily Newsletter", content_text)
        if not success:
            return jsonify({"error": message}), 500

        return jsonify({"message": "Newsletter sent to first user successfully"})

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)