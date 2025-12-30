import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    print("Testing gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
