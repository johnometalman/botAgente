import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Notion API details
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

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

def extract_item_details(item):
    """Extract relevant fields from a Notion database item."""
    properties = item.get("properties", {})
    
    # Extract fields
    role = properties.get("Role", {}).get("title", [{}])[0].get("text", {}).get("content", "No Role")
    startup = properties.get("Startup", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Startup")
    location = properties.get("Location", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No Location")
    remote = properties.get("Remote", {}).get("select", {}).get("name", "No Remote Info")
    vertical = properties.get("Vertical", {}).get("select", {}).get("name", "No Vertical Info")
    ai_summary = properties.get("AI summary", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "No AI Summary")
    apply_url = properties.get("Apply URL", {}).get("url", "No Apply URL")
    send_status = properties.get("Send Status ", {}).get("status", {}).get("name", "No Send Status")

    return {
        "Role": role,
        "Startup": startup,
        "Location": location,
        "Remote": remote,
        "Vertical": vertical,
        "AI Summary": ai_summary,
        "Apply URL": apply_url,
        "Send Status": send_status
    }

def print_item_details(item_details):
    """Print the details of a Notion database item."""
    print("\n📄 Item Details:")
    print("----------------")
    for key, value in item_details.items():
        print(f"- {key}: {value}")

def main():
    # Retrieve data from Notion
    notion_data = query_notion_database()
    if notion_data:
        for item in notion_data.get("results", []):
            # Extract and print details for each item
            item_details = extract_item_details(item)
            print_item_details(item_details)

if __name__ == "__main__":
    main()