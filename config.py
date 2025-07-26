# config.py
import os
from dotenv import load_dotenv

# --- Get the absolute path to the directory this file is in ---
# This makes the script location-independent.
basedir = os.path.abspath(os.path.dirname(__file__))

# --- Construct the full path to the .env file ---
# This ensures we always find AppSettings.env in the project root.
env_path = os.path.join(basedir, 'AppSettings.env')

# --- Load the environment variables from the specified path ---
load_dotenv(dotenv_path=env_path)

# --- Fetch credentials from environment variables ---
gemini_api_key = os.getenv('Gemini_Api_Key')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

# --- Critical Validation ---
# Stop the app immediately if essential keys are missing.
if not gemini_api_key:
    raise ValueError("❌ ERROR: 'Gemini_Api_Key' not found or is empty in your AppSettings.env file.")
if not all([db_name, db_user, db_password, db_host, db_port]):
    raise ValueError("❌ ERROR: One or more database variables (DB_NAME, DB_USER, etc.) are missing from your AppSettings.env file.")

# --- Database Connection Parameters Dictionary ---
# This dictionary will now be correctly populated with your Neon credentials.
DB_PARAMS = {
    'dbname': db_name,
    'user': db_user,
    'password': db_password,
    'host': db_host,
    'port': db_port
}