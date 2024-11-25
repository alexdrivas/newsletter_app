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

    PRODUCTION_DB_USER = os.getenv('PRODUCTION_DB_USER')
    PRODUCTION_DB_PASS = os.getenv('PRODUCTION_DB_PASS')
    PRODUCTIONDB_HOST = os.getenv('PRODUCTIONDB_HOST')
    PRODUCTION_DB_DATABASE = os.getenv('PRODUCTION_DB_DATABASE')
    PRODUCTION_DB_PORT = os.getenv('PRODUCTION_DB_PORT')

    #API_KEY
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')

    # If the PostgreSQL environment variables are not available, fallback to SQLite
    #SQLALCHEMY_DATABASE_URI = os.getenv(
        #'SQLALCHEMY_DATABASE_URI',
        #f'postgresql://{DB_USER}@{DB_HOST}/{DB_DATABASE}'
    #)
    #SupaDB
    
    #SQLALCHEMY_DATABASE_URI = (
    #    f'postgresql://{PRODUCTION_DB_USER}:{PRODUCTION_DB_PASS}@{PRODUCTIONDB_HOST}:{PRODUCTION_DB_PORT}/{PRODUCTION_DB_DATABASE}'
    #)

    SQLALCHEMY_DATABASE_URI = f'postgresql://postgres.yymbexbanxaleynzbylj:{PRODUCTION_DB_PASS}@aws-0-us-west-1.pooler.supabase.com:6543/postgres?gssencmode=disable'
    
    # Print out the variables for debugging
