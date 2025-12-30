import putergenai
import os
import asyncio
import base64
import mimetypes

from dotenv import load_dotenv

load_dotenv()

async def test_vision_ocr():
    try:
        username = os.getenv("PUTER_USERNAME")
        password = os.getenv("PUTER_PASSWORD")
        
        async with putergenai.PuterClient(username, password) as client:
            await client.login(username, password)
            print("Login successful.")
            
            # Use a dummy image or real one if exists
            image_path = "test_image.png"
            if not os.path.exists(image_path):
                 with open("test_image.png", "wb") as f:
                    f.write(os.urandom(1024))
            
            # Encode to base64
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type: mime_type = "image/png"
            
            with open(image_path, "rb") as f:
                base64_img = base64.b64encode(f.read()).decode('utf-8')
            
            data_url = f"data:{mime_type};base64,{base64_img}"
            
            print("Sending Chat request with image...")
            # Using a vision capable model
            # gpt-4o-mini is cost effective and good
            response = await client.ai_chat(
                prompt="Extract all text from this image directly. No markdown formatting, just the text.",
                image_url=data_url,
                options={"model": "gpt-4o-mini"} # or gpt-4o
            )
            
            print(f"Response: {response}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vision_ocr())
