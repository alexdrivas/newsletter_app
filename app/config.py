import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    #MAIL_USE_SSL= os.getenv('MAIL_USE_SSL')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Get the database URI from environment variables
    DB_HOST = os.getenv('DB_HOST')
    DB_DATABASE = os.getenv('DB_DATABASE')
    DB_USER = os.getenv('DB_USER')

    # If the PostgreSQL environment variables are not available, fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        f'postgresql://{DB_USER}@{DB_HOST}/{DB_DATABASE}'
    )
    # Print out the variables for debugging
    print("SQLALCHEMY_DATABASE_URI:", SQLALCHEMY_DATABASE_URI)
    print("MAIL_SERVER:", MAIL_SERVER)
    print("MAIL_PORT:", MAIL_PORT)
    print("MAIL_USERNAME:", MAIL_USERNAME)
    print("MAIL_USE_TLS:", MAIL_USE_TLS)
    print("MAIL_DEFAULT_SENDER:", MAIL_DEFAULT_SENDER)
