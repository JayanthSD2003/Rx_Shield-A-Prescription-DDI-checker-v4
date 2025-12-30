import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")
print("sys.path:")
for p in sys.path:
    print(p)

try:
    import kagglehub
    print("Imported kagglehub successfully")
    print(f"File: {kagglehub.__file__}")
except ImportError as e:
    print(f"Failed to import kagglehub: {e}")

try:
    import requests
    print("Imported requests successfully")
except ImportError as e:
    print(f"Failed to import requests: {e}")
