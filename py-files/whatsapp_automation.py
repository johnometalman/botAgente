import os
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import time

# Load environment variables from .env file
load_dotenv()

# Debugging: Print environment variables
print("NOTION_TOKEN:", os.getenv("NOTION_TOKEN"))
print("DATABASE_ID:", os.getenv("DATABASE_ID"))
print("WHATSAPP_GROUP_NAME:", os.getenv("WHATSAPP_GROUP_NAME"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SEND_STATUS_KEY = "Send Status "
NOTION_API_VERSION = "2022-06-28"

# Notion API details
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
WHATSAPP_GROUP_NAME = os.getenv("WHATSAPP_GROUP_NAME")  # Name of the WhatsApp group

# Validate environment variables
if not all([NOTION_TOKEN, DATABASE_ID, WHATSAPP_GROUP_NAME]):
    logger.error("Missing required environment variables.")
    exit(1)

# Path to ChromeDriver
CHROMEDRIVER_PATH = r'C:\Users\ACER\Documents\Coding Projects Windows\agenteWhastapp\chromedriver-win64\chromedriver.exe'

# Set up Selenium WebDriver
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service)

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
    """Send a message to the WhatsApp group using Selenium."""
    try:
        # Open WhatsApp Web
        driver.get('https://web.whatsapp.com')
        logger.info("Please scan the QR code to log in.")
        time.sleep(15)  # Wait for user to scan QR code manually

        # Locate the group chat by searching for the group name
        search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.send_keys(WHATSAPP_GROUP_NAME)
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)

        # Wait for the chat to load
        time.sleep(2)

        # Locate the message input box and send the message
        message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="1"]')
        message_box.send_keys(message)
        message_box.send_keys(Keys.ENTER)

        # Wait for the message to be sent
        time.sleep(5)

        logger.info("Message sent successfully!")
        return True
    except Exception as e:
        logger.error(f"Error sending message to WhatsApp group: {e}")
        return False
    finally:
        # Close the browser
        driver.quit()

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
            logger.debug(f"Debug - Send Status: '{send_status}'")
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