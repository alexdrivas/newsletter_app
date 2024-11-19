import requests
from app.models import User, SubscriptionContent
from datetime import datetime, time
import os
from app import db 
import logging

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
        categories = "business,tech,politics"
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
                return json_response, None  # Return the updated dictionary
            else:
                return {}, "No news found."
        else:
            return {}, f"API call failed with status code {response.status_code}: {response.text}"
    except Exception as e:
        return {}, f"Error fetching news: {str(e)}"




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


def fetch_news_from_db(language):
    """
    Fetch news data from the database for a given language and limit, ensuring both 
    arguments are present anywhere within the result JSON.

    Args:
        language (str): Language to search for in the JSON result.

    Returns:
        tuple: (news_data (dict), error_message (str))
    """
    try:
        news_data = db.session.query(SubscriptionContent).filter(
            SubscriptionContent.subscription_type == 'NewsTopStories',
            SubscriptionContent.result.contains({"language": language}),
        ).order_by(SubscriptionContent.fetch_date.desc()).first()

        if news_data:
            return news_data.result, None
        else:
            return None, "No news data found matching the criteria."
    except Exception as e:
        return None, f"Error fetching news data: {str(e)}"


def format_HTML_news_container(news_data):
    """
    Formats news results into an HTML container.

    Args:
        news_data (dict): Dictionary containing news results.

    Returns:
        str: HTML formatted news data.
    """
    try:
        # Initialize an empty string to accumulate all HTML content
        html_content = ""
        
        # Iterate through each article in the 'data' list
        for article in news_data.get("data", []):
            # Extract the necessary details from the article
            title = article.get("title", "Unknown title")
            description = article.get("description", "N/A")
            published_at = article.get("published_at", "N/A")
            url = article.get("url", "Unknown url")
            source = article.get("source", "Unknown source")
            image_url = article.get("image_url", "")  # Optional image
            categories = ", ".join(article.get("categories", []))  # Join categories into a string
            
            # Build the HTML content for this article
            html_content += f"""
            <div>
                <h2>News Update</h2>
                <p><strong>Headline:</strong> {title}</p>
                <p>{description}</p>
                <p><strong>Source:</strong> {source}</p>
                <p><strong>Published on:</strong> {published_at}</p>
                <p><strong>Categories:</strong> {categories}</p>
                <p><strong>Read more:</strong> <a href="{url}" target="_blank">Click here</a></p>
            """
            
            # Optionally add an image if available
            if image_url:
                html_content += f'<p><img src="{image_url}" alt="Article Image" style="max-width: 100%; height: auto;"></p>'
            
            # Close the div for the current article
            html_content += "</div><hr>"
        
        # Return the accumulated HTML content
        return html_content
    
    except Exception as e:
        logger.error("Error formatting news container: %s", str(e))
        return "<div>Error formatting news data.</div>"

