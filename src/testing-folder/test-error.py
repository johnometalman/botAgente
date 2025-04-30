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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    if "title" in prop and prop.get("title") and len(prop["title"]) > 0:
        return prop["title"][0].get("text", {}).get("content", default)
    elif "rich_text" in prop and prop.get("rich_text") and len(prop["rich_text"]) > 0:
        return prop["rich_text"][0].get("text", {}).get("content", default)
    elif "select" in prop and prop.get("select"):
        return prop["select"].get("name", default)
    elif "status" in prop and prop.get("status"):
        return prop["status"].get("name", default)
    elif "url" in prop:
        return prop.get("url", default)
    return default

def format_message(item: Dict[str, Any]) -> str:
    """Format the message using the provided template."""
    properties = item.get("properties", {})
    role = get_property_value(properties, "Role", "No Role")
    startup = get_property_value(properties, "Startup", "No Startup")
    location = get_property_value(properties, "Location", "No Location")
    remote = get_property_value(properties, "Remote", "No Remote Info")
    vertical = get_property_value(properties, "Vertical", "No Vertical Info")
    ai_summary = get_property_value(properties, "AI summary", "No AI Summary")
    apply_url = get_property_value(properties, "Apply URL", "No Apply URL")

    # Format the message
    message = (
        f"📢 *Nueva oportunidad de trabajo*\n\n"
        f"- 🔹 *Rol:* {role}\n\n"
        f"- 🏢 *Startup:* {startup}\n"
        f"- 🌍 *Ubicación:* {location} ({remote})\n"
        f"- 📂 *Vertical:* {vertical}\n"
        f"- 🤖 *Resumen:* {ai_summary}\n\n"
        f"- 📩 *Aplica aquí:* {apply_url}"
    )
    return message

def send_to_whatsapp_group(message: str) -> bool:
    """Send a message to the WhatsApp group using pywhatkit with better verification."""
    try:
        logger.info("Preparing to send message to WhatsApp group...")
        
        # Give WhatsApp Web time to load properly
        time.sleep(5)
        
        # Send message with increased wait times
        kit.sendwhatmsg_to_group_instantly(
            group_id=WHATSAPP_GROUP_ID,
            message=message,
            wait_time=10,  # Increased to 10 seconds
            tab_close=False  # Keep tab open so we can verify
        )
        
        # Additional wait to ensure message gets sent
        logger.info("Message sent to WhatsApp Web, waiting for delivery...")
        time.sleep(8)  # Wait for message to send
        
        # Close tab after verification
        logger.info("Closing WhatsApp tab...")
        import pyautogui
        pyautogui.hotkey('ctrl', 'w')
        
        logger.info("Message sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Error sending message to WhatsApp group: {e}")
        try:
            # Try to close any open tabs from failed attempts
            import pyautogui
            pyautogui.hotkey('ctrl', 'w')
        except:
            pass
        return False

def update_notion_status(page_id: str, status: str) -> bool:
    """Update the 'Send Status' in Notion to the specified status."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "properties": {
            SEND_STATUS_KEY: {
                "status": {
                    "name": status
                }
            }
        }
    }
    try:
        response = requests.patch(url, headers=HEADERS, json=data)
        response.raise_for_status()
        logger.info(f"Updated Send Status for page {page_id} to '{status}'")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating Send Status to '{status}': {e}")
        return False

def is_whatsapp_web_ready() -> bool:
    """Check if WhatsApp Web is properly logged in."""
    try:
        import pyautogui
        import webbrowser
        
        # Open WhatsApp Web
        webbrowser.open("https://web.whatsapp.com")
        logger.info("Checking if WhatsApp Web is logged in...")
        
        # Give time for the page to load
        time.sleep(10)
        
        # Look for typical elements of a logged-in WhatsApp Web
        # This is a simple check - might need adjustment
        pyautogui.hotkey('ctrl', 'w')  # Close tab after check
        return True
    except Exception as e:
        logger.error(f"Error checking WhatsApp Web status: {e}")
        return False

def main():
    # Check if WhatsApp Web is ready
    if not is_whatsapp_web_ready():
        logger.error("WhatsApp Web not ready. Please log in to WhatsApp Web first.")
        return
    
    # Retrieve data from Notion
    notion_data = query_notion_database()
    if not notion_data:
        logger.error("Failed to retrieve data from Notion")
        return
        
    # Count records to process
    not_sent_count = 0
    for item in notion_data.get("results", []):
        properties = item.get("properties", {})
        send_status = get_property_value(properties, SEND_STATUS_KEY, "")
        if send_status == "Not Sent":
            not_sent_count += 1
    
    logger.info(f"Found {not_sent_count} records with 'Not Sent' status")
    
    # Process records
    processed_count = 0
    success_count = 0
    error_count = 0
    
    for item in notion_data.get("results", []):
        # Get the current send status
        properties = item.get("properties", {})
        send_status = get_property_value(properties, SEND_STATUS_KEY, "")
        
        # Process only items with "Not Sent" status
        if send_status == "Not Sent":
            processed_count += 1
            logger.info(f"Processing item {processed_count}/{not_sent_count} with ID: {item['id']}")
            
            try:
                # Format the message
                message = format_message(item)
                logger.info(f"Formatted message for item {item['id']}")
                
                # Attempt to send the message to WhatsApp
                if send_to_whatsapp_group(message):
                    # Update status to "Sent" if successful
                    if update_notion_status(item["id"], "Sent"):
                        success_count += 1
                        logger.info(f"Successfully processed item {item['id']}")
                    else:
                        logger.error(f"Message sent but failed to update Notion status for {item['id']}")
                else:
                    # Update status to "Error Sending" if failed
                    update_notion_status(item["id"], "Error Sending")
                    error_count += 1
                    logger.warning(f"Failed to send message for item {item['id']}")
            except Exception as e:
                # Catch any unexpected errors and mark as "Error Sending"
                logger.error(f"Unexpected error processing item {item['id']}: {str(e)}")
                update_notion_status(item["id"], "Error Sending")
                error_count += 1
            
            # Add a delay between processing items
            if processed_count < not_sent_count:
                delay = 15  # 15 seconds between operations
                logger.info(f"Waiting {delay} seconds before processing next item...")
                time.sleep(delay)
        else:
            logger.debug(f"Skipping item with Send Status: '{send_status}'")
    
    logger.info(f"Processing complete. Processed {processed_count} items, {success_count} successful, {error_count} failed.")

if __name__ == "__main__":
    main()