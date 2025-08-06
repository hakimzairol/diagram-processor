# test_api.py - A standalone script to test the Gemini API call directly.

import os
import requests
import base64
import json
from dotenv import load_dotenv

print("--- Starting API Test Script ---")

# 1. Load Environment Variables
# We load the .env file directly to be certain.
env_path = os.path.join(os.path.dirname(__file__), "C:\\Users\\user\\Documents\\Sem 6\\Dr Zulkifli\\New Project\\diagram-processor\\AppSettings.env")
if not os.path.exists(env_path):
    print(f"❌ FATAL ERROR: AppSettings.env file not found at {env_path}")
    exit()

load_dotenv(dotenv_path=env_path)
api_key = os.getenv('Gemini_Api_Key')

if not api_key:
    print("❌ FATAL ERROR: Gemini_Api_Key not found in AppSettings.env")
    exit()

print(f"✅ API Key loaded successfully. Key starts with: {api_key[:8]}...")

# 2. Prepare Image and Prompt
image_path = "C:\\Users\\user\\Downloads\\testing2.jpg"
prompt_path = "C:\\Users\\user\\Documents\\Sem 6\\Dr Zulkifli\\New Project\\diagram-processor\\prompt.txt" # Using the mind map prompt for this test

if not os.path.exists(image_path):
    print(f"❌ FATAL ERROR: Test image '{image_path}' not found in project folder.")
    exit()
if not os.path.exists(prompt_path):
    print(f"❌ FATAL ERROR: Prompt file '{prompt_path}' not found.")
    exit()

print("✅ Image and Prompt files found.")

try:
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    with open(prompt_path, "r") as prompt_file:
        prompt_text = prompt_file.read()
except Exception as e:
    print(f"❌ FATAL ERROR: Could not read image or prompt file. Error: {e}")
    exit()

print("✅ Image and Prompt prepared for sending.")

# 3. Build the API Request
api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
headers = {'Content-Type': 'application/json'}
payload = {
    "contents": [{
        "parts": [
            {"text": prompt_text},
            {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
        ]
    }],
    "generationConfig": {
        "responseMIMEType": "application/json"
    }
}

# 4. Make the API Call and Print EVERYTHING
print("\n--- Sending request to Google... ---")
print(f"URL: {api_url}")

try:
    response = requests.post(api_url, headers=headers, json=payload)
    
    print(f"\n--- Google's Response ---")
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    print(response.headers)
    print("\nResponse Body (Text):")
    print(response.text) # Print the raw text response from Google

except requests.exceptions.RequestException as e:
    print(f"\n--- A network error occurred ---")
    print(f"Error: {e}")

print("\n--- Test Script Finished ---")