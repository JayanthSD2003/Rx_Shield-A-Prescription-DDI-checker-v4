from PIL import Image
import os

img_path = 'icon.png'
ico_path = 'icon.ico'

if os.path.exists(img_path):
    img = Image.open(img_path)
    # Save as ICO with properly sized sub-images
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Successfully converted {img_path} to {ico_path}")
else:
    print(f"Error: {img_path} not found")
