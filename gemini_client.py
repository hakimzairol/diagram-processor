# gemini_client.py
import config
import requests
import json
import base64

GEMINI_API_KEY = config.gemini_api_key

def get_gemini_response(image_bytes: bytes, prompt_filename: str) -> str:
    """
    Sends an image and a prompt from a specified file to the Gemini API.
    Returns the raw text response from the model.
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key is not configured.")

    try:
        with open(prompt_filename, "r") as f:
            prompt_text = f.read()
    except FileNotFoundError:
        return f'{{"error": "Prompt file not found: {prompt_filename}"}}'
        
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    
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
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_json = response.json()
        
        content = response_json['candidates'][0]['content']['parts'][0]['text']
        return content
        
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return f'{{"error": "HTTP Request failed: {e}"}}'
    except (KeyError, IndexError) as e:
        print(f"Failed to parse Gemini response: {e}")
        return f'{{"error": "Failed to parse Gemini response", "details": "{response.text}"}}'