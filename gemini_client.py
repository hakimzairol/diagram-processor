import base64
import requests
import json
import config

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    

def extract_from_image(base64_str: str, prompt_filepath: str = "prompt.txt") -> dict:
    try:
        with open(prompt_filepath, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found")
        return{}
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_str}}
            ]
        }]
    }
    
    try:
        response = requests.post(config.GEMINI_URL, headers=config.HEADERS,json=payload,timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if'candidates' not in result or not result['candidates']:
            print("❌ Gemini API Error: No candidates found.")
            print("Raw Gemini response:", result)
            return {}
        
        part = result['candidates'][0].get('content', {}).get('parts', [{}])[0]
        if 'text' not in part:
            print("❌ Gemini API Error: No text found in response part.")
            print("Raw Gemini response part:", part)
            return {}
        
        text_output = part['text']
        
        if text_output.strip().startswith("```json"):
            text_output = text_output.strip()[7:-3].strip()
        elif text_output.strip().startswith("```"):
            text_output = text_output.strip()[3:-3].strip()
            
        return json.loads(text_output)
    
    except json.JSONDecodeError:
        print(f"❌ JSONDecodeError: Could not parse Gemini output. Trying to find JSON within the text...")
        
        json_start = text_output.find("{")
        json_end = text_output.rfind("}") + 1
        
        if json_start != -1 and json_end != 0:
            json_str = text_output[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"❌ Fallback failed. Could not parse extracted string: {json_str}")
                return {}
            
        else:
            print(f"❌ No JSON object found in Gemini output: {text_output}")
            return {}
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error interacting with Gemini API: {e}")
        return {}
    except Exception as e:
        print(f"❌ An unexpected error occurred during image extraction: {e}")
        return {}
    
    
        
        
