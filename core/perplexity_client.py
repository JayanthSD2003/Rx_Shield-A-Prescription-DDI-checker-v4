import os
import requests
import json
import re

def clean_ocr_text(ocr_text):
    """
    Uses Perplexity API to extract clean drug names from noisy OCR text.
    Returns a list of strings (drug names).
    Returns None if API is not configured or fails, allowing fallback to heuristic.
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return None 

    url = "https://api.perplexity.ai/chat/completions"
    
    prompt = f"""
    Extract only the exact medication names from the following OCR text from a medical prescription. 
    Ignore dosages, frequencies, dates, doctor names, and garbage text.
    Return ONLY a raw JSON list of strings, like ["Drug A", "Drug B"]. Do not include any other text or markdown formatting.
    
    OCR Text:
    {ocr_text}
    """

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "system", "content": "You are a helpful medical assistant that extracts drug names from text. Return only JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                
                # Cleanup potential markdown code blocks
                content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    drug_list = json.loads(content)
                    if isinstance(drug_list, list):
                        return drug_list
                except json.JSONDecodeError:
                    # Fallback if it returns just a comma separated string
                    # or lines
                    return [line.strip() for line in content.split('\n') if len(line.strip()) > 3]
                    
        return None

    except Exception as e:
        print(f"Perplexity API Error: {e}")
        return None
