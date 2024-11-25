import requests
from app.models import User, SubscriptionContent
from datetime import datetime, timezone, timedelta
import os
from app import db 
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def fetch_news(api_token, limit=10, domains=None, categories=None, language='en'):
    """
    Fetches top news stories from the API.
    
    Args:
        api_token (str): Your API token.
        domains (str or list): A list of domains to fetch news from. Defaults to a predefined list.
        categories (str or list): Categories of news to fetch. Defaults to business, tech, and politics.
        language (str): The language of the articles. Defaults to 'en' for English.
    
    Returns:
        tuple: (news_content (list or dict), error_message (str))
    """
    base_url = "https://api.thenewsapi.com/v1/news/top"
    api_token = os.getenv('NEWS_API_KEY')

    # Set default domains if none provided
    if domains is None:
        domains = "cnn.com,msnbc.com,cnbc.com,nbc.com,nytimes.com,bbc.com,bbc.uk"
    elif isinstance(domains, list):
        domains = ",".join(domains)  # Convert list to comma-separated string
    
    # Set default categories if none provided
    if categories is None:
        categories = "business,tech,"
    elif isinstance(categories, list):
        categories = ",".join(categories)  # Convert list to comma-separated string

    # Construct query parameters
    today_date = datetime.today().strftime('%Y-%m-%d')
    params = {
        "api_token": api_token,
        "limit": limit,
        "published_on": today_date,
        "language": language,
        "categories": categories,
        "search": "us", 
        "domains": domains,
    }

    # Make the API request
    try:
        response = requests.get(base_url, params=params)
        
        # Ensure we check the 'data' key in the response
        if response.status_code == 200:
            json_response = response.json()
            if 'data' in json_response:
                # Remove the 'meta' key if it exists
                json_response.pop('meta', None)
                save_news_data_to_db(json_response)
                return json_response, None  # Return the updated dictionary
            else:
                return {}, "No news found."
        else:
            return {}, f"API call failed with status code {response.status_code}: {response.text}"
    except Exception as e:
        return {}, f"Error fetching news: {str(e)}"


def save_news_data_to_db(news_data):
    try:
        # Create a new SubscriptionContent entry without providing the 'id' field
        new_subscription_content = SubscriptionContent(
            subscription_type="NewsTopStories",  # Example subscription type
            result=news_data,  # Weather data from the API response
            fetch_date=datetime.utcnow()  # Current UTC time
        )
        
        # Add to the session and commit the transaction to save it in the database
        db.session.add(new_subscription_content)
        db.session.commit()
        logging.info("News data saved successfully")

    except SQLAlchemyError as e:
        # Handle any SQLAlchemy errors (like unique constraint violations)
        db.session.rollback()  # Rollback the transaction if error occurs
        logging.error(f"News fetch failed: Database error: {str(e)}")
        return None, f"Database error: {str(e)}"

    except Exception as e:
        # Handle any other unexpected errors
        logging.error(f"Unexpected error occurred while saving weaNewsther data: {str(e)}")
        return None, f"Error: {str(e)}"

    return new_subscription_content, None  # Return the saved record and no error
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging
def fetch_news_from_db_raw(language='en', categories=None, limit=None):
    """
    Fetch news data using a raw SQL query with filtering for language, categories, and limit.
    """
    if categories is None:
        categories = ['general']  # Default category if none provided

    try:
        # Get today's date in UTC
        utc_now = datetime.utcnow().date()

        # Prepare the query
        query = text(f"""
            SELECT result
            FROM (
                SELECT result
                FROM subscription_content
                WHERE subscription_type = :subscription_type
                AND result->'data'->0->>'language' = :language
                AND result->'data'->0->>'categories' = :categories
                AND fetch_date >= :fetch_date
                ORDER BY fetch_date DESC
            ) sub
            LIMIT :limit
        """)

        parameters = {
            'subscription_type': 'NewsTopStories',
            'language': language,
            'categories': categories[0],  # Use the first category from the list
            'fetch_date': utc_now,
            'limit': limit
        }

        try:
            logger.info("Searching parameters in DB: %s", parameters)
            result = db.session.execute(query, parameters).fetchall()
            db.session.commit()  # Ensure transaction is committed
        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback if there is an error
            logging.error(f"Database error: {e}")

        if result:
            # Process the results
            news_data = [row[0] for row in result]
            logger.info("News data result from DB: %s", news_data)
            return news_data, None
        else:
            return None, "No matching news data found in the database."
    except Exception as e:
        logger.exception("Error fetching news data using raw SQL: %s", str(e))
        return None, f"Error fetching news data: {str(e)}"





def normalize_news_data(news_data):
    """
    Normalizes news data into a list of articles for consistent processing.

    Args:
        news_data (dict): The news data (API or local).

    Returns:
        list: A list of articles in a consistent format.
    """
    # Check if the news_data is a dictionary with a 'data' key that contains the list
    if isinstance(news_data, dict) and 'data' in news_data:
        # Return the list inside the 'data' key
        return news_data['data']
    else:
        # If there's no 'data' key or it's not in the correct format, return an empty list
        return []


def format_HTML_news_container(articles):
    """
    Formats news results into an HTML container with an improved layout and readability.
    Args:
        articles (list): List of dictionaries containing news article data.
    Returns:
        str: HTML formatted news data.
    """
    try:
        # Initialize the main container
        html_content = """
        <div style="font-family: 'Arial', sans-serif; color: #333; padding: 10px; background-color: #FFF; max-width: 600px; margin: 0 auto;">
        """

        # Add a header for the news section
        html_content += """
        <div style="text-align: left; margin-bottom: 15px; border-bottom: 1px solid #EAEAEA; padding-bottom: 10px;">
            <h1 style="font-size: 18px; margin: 0; color: #222;">News</h1>
        </div>
        """

        # Loop through each article and format the content
        for article in articles:
            title = article.get("title", "Unknown title")
            description = article.get("description", "N/A")
            published_at = article.get("published_at", "N/A")
            url = article.get("url", "#")
            source = article.get("source", "Unknown source")
            image_url = article.get("image_url", "")

            # Remove .com from source
            source = remove_suffix(source)

            published_at = format_datetime_to_est(published_at)
            # Create the article block
            html_content += f"""
            <div style="display: flex; align-items: flex-start; margin-bottom: 10px; padding: 8px; border-bottom: 1px solid #EAEAEA;">

                <!-- Image Section -->
                {"<div style='flex: 0 0 100px; margin-right: 10px;'><img src='" + image_url + "' alt='Article Image' style='width: 80px; height: 80px; object-fit: cover; border-radius: 4px;'></div>" if image_url else ""}

                <!-- Text Section -->
                <div style="flex: 1;">

                    <!-- Title -->
                    <h2 style="font-size: 16px; margin: 0 0 5px; color: #222; font-weight: bold; line-height: 1.2;">{title}</h2>

                    <!-- Description -->
                    <p style="font-size: 11px; color: #666; margin: 0 0 8px; line-height: 1.4;">{description}</p>

                    <!-- Meta Info -->
                    <p style="font-size: 9px; color: #999; margin: 0;">
                        <span><strong>{source}</strong></span> &bull; <span>{published_at}</span> &bull; <span><a href="{url}" target="_blank" style="display: inline-block; margin-bottom: 2px; padding: 2px 4px; background-color: #CFA488; color: #FFF; font-size: 8px; font-weight: bold; text-decoration: none; border-radius: 4px;">Read More</a></span>
                    </p>
                </div>
            </div>
            """

        # Close the main container
        html_content += "</div>"

        return html_content

    except Exception as e:
        print(f"Error formatting news container: {str(e)}")
        return "<div>Error formatting news data.</div>"

def format_datetime_to_est(timestamp):
    try:
        # Parse the original timestamp (assumes it is in UTC, indicated by "Z")
        dt_utc = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        
        # Convert to EST (UTC-5, or UTC-4 during daylight saving time)
        est_offset = timedelta(hours=-5)  # Adjust for standard time
        dt_est = dt_utc.astimezone(timezone(est_offset))
        
        # Format the date and time without seconds
        return dt_est.strftime("%I:%M %p EST")
    
    except Exception as e:
        print("Error formatting datetime:", str(e))
        return "Invalid date"
    
def remove_suffix(domain: str) -> str:
    # Check if the string ends with '.com'
    if domain.endswith('.com'):
        # Remove the suffix '.com'
        return domain[:-4]  # Slice off the last 4 characters
    return domain  # Return the original string if no '.com'

    
def fetch_source_ids(api_token, categories=None, language='en', page=1):
    """
    Fetches source IDs from the sources API based on categories and other filters.

    Args:
        api_token (str): Your API token.
        categories (str): A comma-separated list of categories (e.g. "business,tech").
        language (str): The language of the sources (default is 'en' for English).
        page (int): The page number to retrieve (default is 1).

    Returns:
        dict: JSON response containing source details.
    """
    base_url = "https://api.thenewsapi.com/v1/news/sources"
    
    # Construct query parameters
    params = {
        "api_token": api_token,
        "language": language,  # Filter to English
        "page": page,
    }
    #categories = "business,tech,politics"
    if categories:
        params["categories"] = categories
    
    # Make the API request
    response = requests.get(base_url, params=params)
    print("Full URL:", response.url)  # Debugging: print the final URL with query parameters
    
    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed with status code {response.status_code}: {response.text}")