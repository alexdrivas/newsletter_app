import requests
from app.models import User, SubscriptionContent
from datetime import datetime, time
from app.services.weather_service import fetch_and_save_weather, fetch_weather_from_db_raw
from app.services.news_service import fetch_news, fetch_news_from_db_raw
import os
from app import db 
import logging


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def subscription_router(user_subscriptions):
    """
    Routes the subscriptions to relevant API functions and sends the API response.

    Args:
        user_subscriptions (list): List of user's subscriptions.

    Returns:
        dict: A dictionary containing the combined results from all APIs.
    """
    logger.info("Started subscription router with %d subscriptions", len(user_subscriptions))
    results = {}

    for sub in user_subscriptions:
        if sub['name'] == 'WeatherUpdateNow':
            location = sub['details'].get('location')
            units = sub['details'].get('units', 'imperial')

            logger.debug("Fetching weather for location: %s, units: %s", location, units)

            # Check the database for existing data
            weather_content, error = fetch_weather_from_db_raw(location)
            if weather_content:
                logger.info("Weather data fetched from database: %s", weather_content)
                results['weather'] = weather_content  # Store as a raw dictionary
            elif error:
                logger.warning("Weather data not found in database: %s", error)
                weather_content, weather_error = fetch_and_save_weather(location, units)
                if weather_error:
                    results['weather'] = {"error": f"Failed to fetch weather: {weather_error}"}
                    logger.error("Weather fetch failed: %s", weather_error)
                else:
                    results['weather'] = weather_content  # Store as a raw dictionary
                    logger.info("Weather fetched successfully: %s", weather_content)


        if sub['name'] == 'NewsTopStories':
            language = sub['details'].get('language', 'en')
            limit = sub['details'].get('limit') # this represents the number of articles the user wants to recieve. 
            categories = sub['details'].get('categories', 'general')
            
            logger.debug("Fetching news for language: %s, limit: %s, categories: %s", language, limit, categories)
            
            # Check the database for existing data
            news_content, error = fetch_news_from_db_raw(language, categories)
            if news_content:
                logger.info("News data fetched from database.")
                results['news'] = news_content
            elif error:
                logger.warning("News data not found in database: %s", error)
                news_content, news_error = fetch_news(language, limit)
                if news_error:
                    results['news'] = f"Failed to fetch news: {news_error}"
                    logger.error("News fetch failed: %s", news_error)
                else:
                    results['news'] = news_content
                    logger.info("News fetched successfully: %s", news_content)

    return results