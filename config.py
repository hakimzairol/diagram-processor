import os
from dotenv import load_dotenv

load_dotenv("AppSettings.env")

GEMINI_API_KEY = os.getenv("Gemini_Api_Key")
if not GEMINI_API_KEY:
    raise ValueError("❌ ERROR: Gemini_Api_Key not found in AppSettings.env")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
HEADERS = {"Content-Type": "application/json"}

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

for key, value in DB_PARAMS.items():
    if not value:
        raise ValueError(f"❌ ERROR: Database parameter '{key.upper()}' not found in AppSettings.env")


