
from core.knowledge_graph import KnowledgeGraphManager
import os

kg = KnowledgeGraphManager()
print("Generating Universal Graph...")
path = kg.generate_graph([]) # Default
print(f"Path: {path}")

if start_path := path:
    size = os.path.getsize(start_path)
    print(f"File Size: {size} bytes")
    if size < 1000:
        print("WARNING: File too small, likely empty!")
    else:
        print("SUCCESS: File generated with content.")
