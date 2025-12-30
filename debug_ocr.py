import putergenai
import os
import asyncio
import traceback
from dotenv import load_dotenv

load_dotenv()

async def test_ocr():
    try:
        username = os.getenv("PUTER_USERNAME")
        password = os.getenv("PUTER_PASSWORD")
        
        print(f"Attempting login for: {username}")
        
        async with putergenai.PuterClient(username, password) as client:
            print("Client created.")
            await client.login(username, password)
            print("Login successful.")
            
            # Create a dummy image file (binary)
            with open("test_image.png", "wb") as f:
                f.write(os.urandom(1024)) # Junk data, but should trigger API
            
            # Try with a real file path
            print("Testing ai_img2txt...")
            try:
                # Based on library code:
                # if isinstance(image, str): ... payload = {"image_url": ...}
                # else: ... data.add_field('image', image)
                
                # So we need to pass the file object or bytes
                with open("test_image.png", "rb") as f:
                     # Reading file to bytes first to be safe
                     file_bytes = f.read()
                     text = await client.ai_img2txt(file_bytes)
                print(f"Result: {text}")
                
            except Exception as e:
                print("\n!!! ERROR CAUGHT !!!")
                print(f"Type: {type(e)}")
                print(f"Message: {str(e)}")
                print("Traceback:")
                traceback.print_exc()

    except Exception as e:
        print(f"Outer Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ocr())
