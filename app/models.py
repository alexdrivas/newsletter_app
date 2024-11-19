from app import db  # Import db from your app setup
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date



# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=date.today())
    subscriptions = db.Column(JSONB, nullable=False, default={})

    def __init__(self, first_name, last_name, email, subscriptions=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.subscriptions = subscriptions or {}

    def __repr__(self):
        return f"<User {self.email}>"

# SubscriptionContent Model
class SubscriptionContent(db.Model):
    __tablename__ = 'subscription_content'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subscription_type = db.Column(db.String(50), nullable=False)  # E.g., 'WeatherUpdateNow'
    result = db.Column(db.JSON, nullable=False)  # API response stored as JSON
    fetch_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, subscription_type, result, fetch_date=None):
        self.subscription_type = subscription_type
        self.result = result
        self.fetch_date = fetch_date or datetime.utcnow()

    def __repr__(self):
        return f"<SubscriptionContent {self.subscription_type} at {self.fetch_date}>"
