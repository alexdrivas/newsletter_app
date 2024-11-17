from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_mail import Mail
from flask_migrate import Migrate
from app.config import Config
import logging

# Initialize the db and mail
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.DEBUG,  # Log all levels DEBUG and above
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.StreamHandler(),  # Output to console
                            logging.FileHandler('app.log')  # Log to a file
                        ])

    # Load configuration from .env or config.py
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register blueprints
    from .routes import main_routes, user_routes, email_routes
    app.register_blueprint(main_routes.main_bp)
    app.register_blueprint(user_routes.user_bp)
    app.register_blueprint(email_routes.email_bp)

    return app
