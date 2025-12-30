import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API Key found")
    exit()

genai.configure(api_key=api_key)

print(f"Testing model: gemini-2.5-flash-live")
try:
    # Try to initialize
    model = genai.GenerativeModel('gemini-2.5-flash-live')
    print("Initialization successful. Attempting generation...")
    
    # Try a simple generation
    response = model.generate_content("Test")
    print(f"Generation response: {response.text}")
    print("SUCCESS: Model exists and is working.")
except Exception as e:
    print(f"FAILURE: {e}")
