import os
import logging
import requests
import pywhatkit as kit
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed logs
logger = logging.getLogger(__name__)

# Constants
SEND_STATUS_KEY = "Send Status"  # Must match exactly with Notion property name
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
        logger.debug("Querying Notion database...")
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying Notion database: {str(e)}")
        logger.debug(f"Response content: {e.response.text if e.response else ''}")
        return None

def get_property_value(properties: Dict[str, Any], key: str, default: str = "") -> str:
    """Extract property values from Notion properties with enhanced status handling."""
    prop = properties.get(key, {})
    logger.debug(f"Raw property data for '{key}': {json.dumps(prop, indent=2)}")
    
    # Handle status property explicitly
    if prop.get("type") == "status":
        return prop.get("status", {}).get("name", default)
    
    # Handle other property types
    type_handlers = {
        "title": lambda: prop["title"][0]["text"]["content"],
        "rich_text": lambda: prop["rich_text"][0]["text"]["content"],
        "select": lambda: prop["select"]["name"],
        "url": lambda: prop["url"]
    }
    
    for prop_type, handler in type_handlers.items():
        if prop_type in prop:
            try:
                return handler()
            except (KeyError, IndexError):
                logger.warning(f"Malformed {prop_type} property for key '{key}'")
                return default
    
    return default

def format_message(item: Dict[str, Any]) -> str:
    """Format the message using the provided template."""
    properties = item.get("properties", {})
    return (
        f"📢 *Nueva oportunidad de trabajo*\n\n"
        f"- 🔹 *Rol:* {get_property_value(properties, 'Role', 'No Role')}\n\n"
        f"- 🏢 *Startup:* {get_property_value(properties, 'Startup', 'No Startup')}\n"
        f"- 🌍 *Ubicación:* {get_property_value(properties, 'Location', 'No Location')} "
        f"({get_property_value(properties, 'Remote', 'No Remote Info')})\n"
        f"- 📂 *Vertical:* {get_property_value(properties, 'Vertical', 'No Vertical Info')}\n"
        f"- 🤖 *Resumen:* {get_property_value(properties, 'AI summary', 'No AI Summary')}\n\n"
        f"- 📩 *Aplica aquí:* {get_property_value(properties, 'Apply URL', 'No Apply URL')}"
    )

def send_to_whatsapp_group(message: str) -> bool:
    """Send a message to the WhatsApp group with enhanced error handling."""
    try:
        logger.debug("Initializing WhatsApp Web...")
        kit.sendwhatmsg_to_group_instantly(
            group_id=WHATSAPP_GROUP_ID,
            message=message,
            wait_time=15,  # Increased for reliability
            tab_close=True
        )
        logger.info("Message sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        return False

def update_send_status(page_id: str, status: str) -> bool:
    """Update the Send Status property in Notion with thorough error handling."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            SEND_STATUS_KEY: {
                "status": {
                    "name": status
                }
            }
        }
    }
    
    try:
        logger.debug(f"Attempting to update status to '{status}' for page {page_id}")
        response = requests.patch(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully updated status to '{status}' for page {page_id}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Status update failed: {str(e)}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        logger.debug(f"Response content: {e.response.text if e.response else ''}")
        return False

def main():
    """Main execution flow with comprehensive logging."""
    logger.info("Starting script execution...")
    
    notion_data = query_notion_database()
    if not notion_data or not notion_data.get("results"):
        logger.warning("No data found in Notion database")
        return

    processed_count = 0
    for item in notion_data.get("results", []):
        item_id = item.get("id", "unknown")
        logger.debug(f"Processing item {item_id}")
        
        properties = item.get("properties", {})
        send_status = get_property_value(properties, SEND_STATUS_KEY)
        
        logger.debug(f"Item {item_id} properties:\n{json.dumps(properties, indent=2)}")
        logger.info(f"Current Send Status for {item_id}: '{send_status}'")

        if send_status == "Not Sent":
            logger.info(f"Processing item {item_id} with status 'Not Sent'")
            try:
                message = format_message(item)
                logger.debug(f"Formatted message:\n{message}")
                
                if send_to_whatsapp_group(message):
                    update_send_status(item_id, "Sent")
                else:
                    update_send_status(item_id, "Error Sending")
                
                processed_count += 1
            except Exception as e:
                logger.error(f"Critical error processing item {item_id}: {str(e)}")
                update_send_status(item_id, "Error Sending")
        else:
            logger.info(f"Skipping item {item_id} (Status: '{send_status}')")

    logger.info(f"Processing complete. {processed_count} items processed.")

if __name__ == "__main__":
    main()