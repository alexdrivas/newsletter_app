import requests
from app.models import User, SubscriptionContent
from datetime import datetime, time
import os
from app import db 
import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def fetch_news(api_token, limit=1, domains=None, categories=None, language='en'):
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

    # Default to limit of 1 if not provided
    if limit is None:
        limit = 1

    # Set default domains if none provided
    if domains is None:
        domains = "cnn.com,msnbc.com,cnbc.com,nbc.com,nytimes.com,bbc.com,bbc.uk"
    elif isinstance(domains, list):
        domains = ",".join(domains)  # Convert list to comma-separated string
    
    # Set default categories if none provided
    if categories is None:
        categories = "cars,driver,business,tech,politics"
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
        print("Request URL:", base_url, params)
        
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




def fetch_news_from_db():
    """
    Fetch news data from the database for a given language using JSONB path queries.

    Args:
        language (str): Language to search for in the JSON result.

    Returns:
        tuple: (news_data (dict), error_message (str))
    """
    try:

        # Get today's date in UTC (using datetime's built-in timezone support)
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        today = utc_now.date()

        # Query using jsonb_path_exists to check for language anywhere in the JSON
        news_data = db.session.query(SubscriptionContent).filter(
            SubscriptionContent.subscription_type == 'NewsTopStories',
            # Ensure that fetch_date is in UTC timezone and compare only the date part
            SubscriptionContent.fetch_date >= datetime.today().date()
        ).order_by(SubscriptionContent.fetch_date.desc()).first()

        if news_data:
            return news_data.result, None
        else:
            return None, "No news data found matching the criteria."
    except Exception as e:
        return None, f"Error fetching news data: {str(e)}"

def normalize_news_data(news_data):
    """
    Normalizes news data into a list of articles for consistent processing.

    Args:
        news_data (dict): The news data (API or local).

    Returns:
        list: A list of articles in a consistent format.
    """
    # Check if 'data' is a list or a dictionary and normalize it into a list
    if isinstance(news_data.get("data"), list):
        return news_data["data"]
    elif isinstance(news_data.get("data"), dict):
        return [news_data["data"]]  # Convert single article into a list
    else:
        return []  # In case of unexpected data structure

def format_HTML_news_container(news_data):
    """
    Formats news results into an HTML container.

    Args:
        news_data (dict): Dictionary containing news results.

    Returns:
        str: HTML formatted news data.
    """
    try:
        # Normalize the data into a list of articles
        articles = normalize_news_data(news_data)

        # Initialize an empty string to accumulate all HTML content
        html_content = ""

        # Loop through each article and build the HTML
        for article in articles:
            # Extract the necessary details from the article
            title = article.get("title", "Unknown title")
            description = article.get("description", "N/A")
            published_at = article.get("published_at", "N/A")
            url = article.get("url", "Unknown url")
            source = article.get("source", "Unknown source")
            image_url = article.get("image_url", "")  # Optional image
            categories = ", ".join(article.get("categories", []))  # Join categories into a string

            # Reformat time to EST (assumes format_datetime_to_est function exists)
            published_at = format_datetime_to_est(published_at)

            # Build the HTML content for this article
            html_content += f"""
            <div>
                <h2>News Update</h2>
                <p>Published: {published_at}</p>
                <p><strong>Headline:</strong> {title}.</p>
                <p>{description}</p>
                <p><strong>Source:</strong> {source}</p>
                <p><a href="{url}" target="_blank">Read more</a></p>
            """

            # Optionally add an image if available
            if image_url:
                html_content += f'<p><img src="{image_url}" alt="Article Image" style="max-width: 50%; height: auto;"></p>'

            # Close the div for the current article
            html_content += "</div><hr>"

        # Return the accumulated HTML content
        return html_content

    except Exception as e:
        logger.error("Error formatting news container: %s", str(e))
        return "<div>Error formatting news data.</div>"

from datetime import datetime, timezone, timedelta

def format_datetime_to_est(timestamp):
    try:
        # Parse the original timestamp (assumes it is in UTC, indicated by "Z")
        dt_utc = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        
        # Convert to EST (UTC-5, or UTC-4 during daylight saving time)
        est_offset = timedelta(hours=-5)  # Adjust for standard time
        dt_est = dt_utc.astimezone(timezone(est_offset))
        
        # Format the date and time without seconds
        return dt_est.strftime("%Y-%m-%d %I:%M %p EST")
    
    except Exception as e:
        print("Error formatting datetime:", str(e))
        return "Invalid date"