import os
import requests
import pywhatkit as kit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Notion API details
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",  # Use the latest version
    "Content-Type": "application/json"
}

def query_notion_database():
    """Fetch data from the Notion database."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

def format_message(item):
    """Format the message using the provided template."""
    properties = item.get("properties", {})
    role = properties.get("Role", {}).get("title", [{}])[0].get("text", {}).get("content", "No Role")
    startup = properties.get("Startup", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Startup")
    location = properties.get("Location", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Location")
    remote = properties.get("Remote", {}).get("select", {}).get("name", "No Remote Info")
    vertical = properties.get("Vertical", {}).get("select", {}).get("name", "No Vertical Info")
    ai_summary = properties.get("AI summary", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No AI Summary")
    apply_url = properties.get("Apply URL", {}).get("url", "No Apply URL")

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

def send_to_whatsapp_number(message):
    """Send a message to a WhatsApp number."""
    try:
        # Send the message immediately
        kit.sendwhatmsg_instantly(phone_no=WHATSAPP_NUMBER, message=message, wait_time=15, tab_close=True)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

def update_send_status(page_id):
    """Update the 'Send Status' to 'Sent' in Notion."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    data = {
        "properties": {
            "Send Status ": {  # Note the trailing space
                "status": {
                    "name": "Sent"
                }
            }
        }
    }
    response = requests.patch(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"Updated Send Status for page {page_id}")
    else:
        print(f"Error updating Send Status: {response.status_code}, {response.text}")

def main():
    # Retrieve data from Notion
    notion_data = query_notion_database()
    if notion_data:
        for item in notion_data.get("results", []):
            send_status = item.get("properties", {}).get("Send Status ", {}).get("status", {}).get("name", "")
            print(f"Debug - Send Status: '{send_status}'")  # Debug line
            if send_status == "Not Sent":
                # Format the message
                message = format_message(item)
                # Send the message to WhatsApp
                send_to_whatsapp_number(message)
                # Update the "Send Status" to "Sent" in Notion
                update_send_status(item["id"])
            else:
                print(f"Skipping item with Send Status: '{send_status}'")

if __name__ == "__main__":
    main()