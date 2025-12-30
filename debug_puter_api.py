import putergenai
import os
from dotenv import load_dotenv

load_dotenv()

try:
    username = os.getenv("PUTER_USERNAME")
    password = os.getenv("PUTER_PASSWORD")
    
    print(f"User: {username}")
    
    client = putergenai.PuterClient(username, password)
    print("Client created.")
    print("Client attributes:", dir(client))
    
    # Check if 'ai' is nested deeper or under a different name
    if hasattr(client, 'chat'):
        print("client.chat attributes:", dir(client.chat))
        
except Exception as e:
    print(f"Error: {e}")
