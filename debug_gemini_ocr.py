import asyncio
import os
from core.gemini_client import perform_ocr_gemini, analyze_prescription

# Mock an image path - user needs to provide one or we use a dummy
# Ideally we search for a png/jpg in the dir.

def test_gemini():
    print("Testing Gemini OCR...")
    
    # improved: find first image file in current dir
    image_path = None
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.abspath(file)
            break
            
    if not image_path:
        print("No image found in current directory to test.")
        return

    print(f"Using image: {image_path}")
    
    # Test Raw OCR
    print("\n--- Raw OCR ---")
    text = perform_ocr_gemini(image_path)
    print(text[:500] + "..." if len(text) > 500 else text)
    
    # Test Full Analysis
    # print("\n--- Full Analysis ---")
    # result = analyze_prescription(image_path)
    # print(result)

if __name__ == "__main__":
    test_gemini()
