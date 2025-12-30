import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def perform_ocr_rapidapi(image_path):
    """
    Sends an image to RapidAPI 'OCR AI' for text extraction.
    Returns the extracted text as a string.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    api_host = os.getenv("RAPIDAPI_HOST", "ocr-ai.p.rapidapi.com")

    if not api_key:
        raise ValueError("RAPIDAPI_KEY not found in environment variables.")

    url = f"https://{api_host}/request/analyze"
    
    # Check if image exists
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"

    import mimetypes
    
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = 'image/jpeg' # Fallback default
            
        with open(image_path, "rb") as image_file:
            files = {"file": (os.path.basename(image_path), image_file, mime_type)}
            headers = {
                "x-rapidapi-key": api_key,
                "x-rapidapi-host": api_host
            }
            
            # Note: RapidAPI examples often don't set Content-Type for multipart/form-data manually,
            # requests library handles it when 'files' is passed.
            response = requests.post(url, files=files, headers=headers)
            
            if response.status_code != 200:
                return f"Error: RapidAPI returned status {response.status_code}. {response.text}"
            
            try:
                data = response.json()
                # Parse logic specific to 'OCR AI' response structure
                # Typically data['data']['text'] or similar. 
                # Based on general OCR AI knowledge, let's try to find the text field.
                # If structure is unknown, we dump the whole thing (safer for v1) or try to join lines.
                
                # Heuristic for generic OCR response
                if 'data' in data and 'text' in data['data']:
                     return data['data']['text']
                elif 'text' in data:
                    return data['text']
                
                # Fallback: raw json dump if structure is widely different
                return json.dumps(data, indent=2)

            except json.JSONDecodeError:
                return f"Error: Failed to parse JSON response. Raw: {response.text}"

    except Exception as e:
        return f"Error connecting to RapidAPI: {str(e)}"
