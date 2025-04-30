import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

print("NOTION_TOKEN:", os.getenv("NOTION_TOKEN"))
print("DATABASE_ID:", os.getenv("DATABASE_ID"))
print("WHATSAPP_GROUP_NAME:", os.getenv("WHATSAPP_GROUP_NAME"))
print("WHATSAPP_NUMBER:", os.getenv("WHATSAPP_NUMBER"))
