import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import init_db, add_user, get_user
from core.auth_manager import register, login
from core.gemini_client import perform_ocr, check_ddi

class TestRxShieldCore(unittest.TestCase):
    def setUp(self):
        # Use a test DB
        # Note: In a real scenario, we'd mock the DB or use an in-memory one.
        # Here we'll just use the main one but be careful not to pollute it too much
        # or just test the logic.
        init_db()

    def test_auth_flow(self):
        # Test Registration
        username = "test_user_123"
        password = "password123"
        
        # Clean up if exists
        if get_user(username):
            # We can't easily delete with current API, so we'll use a random suffix
            import random
            username = f"test_user_{random.randint(1000, 9999)}"
        
        success, msg = register(username, password)
        self.assertTrue(success, f"Registration failed: {msg}")
        
        # Test Login
        success, msg = login(username, password)
        self.assertTrue(success, f"Login failed: {msg}")
        
        # Test Invalid Login
        success, msg = login(username, "wrong_password")
        self.assertFalse(success, "Invalid login should fail")

    def test_gemini_client_structure(self):
        # We can't easily test actual API calls without a key and image, 
        # but we can check if functions exist and handle missing key gracefully.
        
        # Check if functions are callable
        self.assertTrue(callable(perform_ocr))
        self.assertTrue(callable(check_ddi))
        
        # Test missing key behavior (assuming key might not be set in env yet)
        if not os.getenv("GEMINI_API_KEY"):
            result = perform_ocr("dummy_path.jpg")
            self.assertIn("Error", result)

if __name__ == '__main__':
    unittest.main()
