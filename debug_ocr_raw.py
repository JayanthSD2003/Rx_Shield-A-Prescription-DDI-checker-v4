import putergenai
import os
import asyncio
import base64
import mimetypes
import json
import struct
import zlib
from dotenv import load_dotenv

load_dotenv()

def create_valid_png(filename):
    width = 1
    height = 1
    bit_depth = 8
    color_type = 2 # RGB
    compression = 0
    filter_method = 0
    interlace = 0
    
    # Signature
    png = b'\x89PNG\r\n\x1a\n'
    
    # IHDR
    ihdr_content = struct.pack('!I I B B B B B', width, height, bit_depth, color_type, compression, filter_method, interlace)
    ihdr = struct.pack('!I', len(ihdr_content)) + b'IHDR' + ihdr_content + struct.pack('!I', zlib.crc32(b'IHDR' + ihdr_content))
    png += ihdr
    
    # IDAT
    raw_data = b'\x00\xff\x00\x00' # Filter 0, Red pixel
    idat_content = zlib.compress(raw_data)
    idat = struct.pack('!I', len(idat_content)) + b'IDAT' + idat_content + struct.pack('!I', zlib.crc32(b'IDAT' + idat_content))
    png += idat
    
    # IEND
    iend_content = b''
    iend = struct.pack('!I', len(iend_content)) + b'IEND' + iend_content + struct.pack('!I', zlib.crc32(b'IEND' + iend_content))
    png += iend
    
    with open(filename, 'wb') as f:
        f.write(png)
    print(f"Created valid PNG: {filename}")

async def test_raw_ocr():
    try:
        username = os.getenv("PUTER_USERNAME")
        password = os.getenv("PUTER_PASSWORD")
        
        async with putergenai.PuterClient(username, password) as client:
            await client.login(username, password)
            print("Login successful.")
            
            image_path = "test_image.png"
            create_valid_png(image_path)
            
            mime_type = "image/png"
            
            with open(image_path, "rb") as f:
                base64_img = base64.b64encode(f.read()).decode('utf-8')
            
            data_url = f"data:{mime_type};base64,{base64_img}"
            
            # Construct raw payload bypassing validation
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
                                {"type": "text", "text": "Describe this image."},
                                {"type": "image_url", "image_url": {"url": data_url}}
                            ]
                        }
                    ],
                    "stream": False
                }
            }
            
            print("Sending Raw Request...")
            session = await client._get_session()
            headers = client._get_auth_headers()
            
            async with session.post(
                f"{client.api_base}/drivers/call",
                json=payload,
                headers=headers
            ) as response:
                print(f"Status: {response.status}")
                if response.status != 200:
                    print(await response.text())
                    return

                resp_json = await response.json()
                
                # SAVE log
                with open("debug_response.json", "w", encoding="utf-8") as logout:
                    json.dump(resp_json, logout, indent=2)

                print("Response JSON saved to debug_response.json")


                if "result" in resp_json:
                     choices = resp_json["result"].get("choices", [])
                     if choices:
                         print("\nExtracted Text:")
                         print(choices[0]["message"]["content"])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_ocr())
