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

def print_database_structure(data):
    """Print the structure of the retrieved data."""
    if data:
        print("Database Structure:")
        print("==================")
        for item in data.get("results", []):
            print("\nItem ID:", item.get("id"))
            print("Properties:")
            for key, value in item.get("properties", {}).items():
                print(f"- {key}: {value}")

def main():
    # Retrieve data from Notion
    notion_data = query_notion_database()
    if notion_data:
        # Print the structure of the data
        print_database_structure(notion_data)

if __name__ == "__main__":
    main()