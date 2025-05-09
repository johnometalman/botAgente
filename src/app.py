import os
import logging
import requests
import pywhatkit as kit
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SEND_STATUS_KEY = "Send Status "
NOTION_API_VERSION = "2022-06-28"

# Notion API details
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID")

# Validate environment variables
if not all([NOTION_TOKEN, DATABASE_ID, WHATSAPP_GROUP_ID]):
    logger.error("Missing required environment variables.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_API_VERSION,
    "Content-Type": "application/json"
}

def query_notion_database() -> Optional[Dict[str, Any]]:
    """Fetch data from the Notion database."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    try:
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion database: {e}")
        return None

def get_property_value(properties: Dict[str, Any], key: str, default: str = "No Info") -> str:
    """Helper function to extract property values from Notion properties."""
    prop = properties.get(key, {})
    if "title" in prop:
        return prop["title"][0].get("text", {}).get("content", default)
    elif "rich_text" in prop:
        return prop["rich_text"][0].get("text", {}).get("content", default)
    elif "select" in prop:
        return prop["select"].get("name", default)
    elif "url" in prop:
        return prop.get("url", default)
    return default

def format_message(item: Dict[str, Any]) -> str:
    """Format the message using the provided template."""
    properties = item.get("properties", {})
    role = get_property_value(properties, "Role", "No Role")
    location = get_property_value(properties, "Location", "No Location")
    remote = get_property_value(properties, "Remote", "No Remote Info")
    vertical = get_property_value(properties, "Vertical", "No Vertical Info")
    summary = get_property_value(properties, "Summary", "No Summary")


    # Format the message
    message = (
        f"`{role}`\n\n"
        f"- _{vertical}_\n"
        f"- {location} *({remote})*\n\n"
        f"- {summary}\n\n"
        f"- 📩 *Revisala en:* https://job-posting.super.site/last"
    )
    return message

def send_to_whatsapp_group(message: str) -> bool:
    """Send a message to the WhatsApp group using the group ID."""
    try:
        # Ensure WhatsApp Web has enough time to load
        time.sleep(2)  # Reduced delay to 2 seconds
        kit.sendwhatmsg_to_group_instantly(
            group_id=WHATSAPP_GROUP_ID,
            message=message,
            wait_time=2,  # Reduced wait_time to 2 seconds
            tab_close=True
        )
        logger.info("Message sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Error sending message to WhatsApp group: {e}")
        return False

def update_send_status(page_id: str) -> bool:
    """Update the 'Send Status' to 'Sent' in Notion."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "properties": {
            SEND_STATUS_KEY: {
                "status": {
                    "name": "Sent"
                }
            }
        }
    }
    try:
        response = requests.patch(url, headers=HEADERS, json=data)
        response.raise_for_status()
        logger.info(f"Updated Send Status for page {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating Send Status: {e}")
        return False

def main():
    # Retrieve data from Notion
    notion_data = query_notion_database()
    if notion_data:
        for item in notion_data.get("results", []):
            send_status = item.get("properties", {}).get(SEND_STATUS_KEY, {}).get("status", {}).get("name", "")
            if send_status == "Not Sent":
                # Format the message
                message = format_message(item)
                # Send the message to WhatsApp
                if send_to_whatsapp_group(message):
                    # Update the "Send Status" to "Sent" in Notion
                    update_send_status(item["id"])
            else:
                logger.info(f"Skipping item with Send Status: '{send_status}'")

if __name__ == "__main__":
    main()