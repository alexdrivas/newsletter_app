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
