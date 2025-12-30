import os
import asyncio
import putergenai
import base64
import mimetypes
import json
from dotenv import load_dotenv

load_dotenv()

def perform_ocr_puter(image_path):
    """
    Sends an image to Puter.js OCR API (via Chat Vision) for text extraction.
    Requires PUTER_USERNAME and PUTER_PASSWORD in environment variables.
    """
    username = os.getenv("PUTER_USERNAME")
    password = os.getenv("PUTER_PASSWORD")

    if not username or not password:
        return "Error: PUTER_USERNAME or PUTER_PASSWORD not found in environment variables."

    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"

    async def _async_ocr():
        try:
            # Initialize client with credentials
            async with putergenai.PuterClient(username, password) as client:
                # Login first to get token
                await client.login(username, password)
                
                # Prepare Image as Base64 Data URI
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type: mime_type = "image/png"
                
                with open(image_path, "rb") as f:
                    base64_img = base64.b64encode(f.read()).decode('utf-8')
                
                data_url = f"data:{mime_type};base64,{base64_img}"
                
                # Construct raw payload for gpt-4o-mini
                payload = {
                    "interface": "puter-chat-completion",
                    "driver": "openai-completion",
                    "method": "complete",
                    "args": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extract all text from this image. Output ONLY the extracted text. Do not add markdown blocks like ``` or any conversational text."},
                                    {"type": "image_url", "image_url": {"url": data_url}}
                                ]
                            }
                        ],
                        "stream": False,
                        "temperature": 0.0
                    }
                }
                
                # Send Raw Request
                session = await client._get_session()
                headers = client._get_auth_headers()
                
                async with session.post(
                    f"{client.api_base}/drivers/call",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return f"Error using AI API: Status {response.status} - {error_text}"
                    
                    resp_json = await response.json()
                    
                    if "result" in resp_json:
                        result = resp_json["result"]
                        # Check for list of choices (standard OpenAI)
                        if "choices" in result and isinstance(result["choices"], list):
                             choices = result.get("choices", [])
                             if choices:
                                 content = choices[0]["message"]["content"]
                                 return content
                        # Check for direct message (Puter adaptation for single choice)
                        elif "message" in result:
                             content = result["message"]["content"]
                             return content
                        else:
                             return f"Error: Unexpected response structure: {json.dumps(resp_json)}"
                    else:
                         return f"Error: Unexpected response format: {json.dumps(resp_json)}"

        except Exception as e:
            # import traceback
            # traceback.print_exc() 
            return f"Error using AI OCR: {str(e)}"

    try:
        # Run async function synchronously
        return asyncio.run(_async_ocr())
    except Exception as e:
        return f"Error running AI OCR: {str(e)}"
