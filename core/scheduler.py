import json
import os
import time
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.core.audio import SoundLoader

class NotificationManager:
    def __init__(self):
        self.settings_file = "user_settings.json"
        self.timings = {
            "breakfast": "08:00",
            "lunch": "13:00",
            "dinner": "20:00",
            "enabled": False
        }
        self.load_settings()
        self.sound = SoundLoader.load('welcome.mp3') # Using existing sound as placeholder or we can use default system beep
        
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.timings.update(data)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self, breakfast, lunch, dinner, enabled):
        self.timings["breakfast"] = breakfast
        self.timings["lunch"] = lunch
        self.timings["dinner"] = dinner
        self.timings["enabled"] = enabled
        
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.timings, f)
            print("Settings saved successfully.")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def start_service(self):
        # Check every 60 seconds
        Clock.schedule_interval(self.check_alerts, 60)
        print("Notification Scheduler Started.")

    def check_alerts(self, dt):
        if not self.timings["enabled"]:
            return

        current_time = time.strftime("%H:%M")
        
        if current_time == self.timings["breakfast"]:
            self.trigger_alert("Breakfast")
        elif current_time == self.timings["lunch"]:
            self.trigger_alert("Lunch")
        elif current_time == self.timings["dinner"]:
            self.trigger_alert("Dinner")

    def schedule_demo_alert(self, delay=10):
        print(f"Scheduling Demo Alert in {delay} seconds...")
        Clock.schedule_once(lambda dt: self.trigger_alert("Test/Demo"), delay)

    def trigger_alert(self, meal_name):
        print(f"TRIGGERING ALERT FOR {meal_name}")
        
        if meal_name == "Test/Demo":
            # specialized demo behavior
            from core.tts_manager import speak_text
            import threading
            import winsound
            import time

            # 1. Voiceover
            speak_text("This is a testing alert.")
            
            # 2. Buzz (in thread to avoid blocking UI)
            def buzz_sequence():
                time.sleep(2.5) # Wait for TTS
                try:
                    winsound.Beep(1000, 2000) # 1000Hz, 2000ms
                except:
                    print("Winsound not available or failed.")
            
            threading.Thread(target=buzz_sequence).start()
            
        else:
            # Standard Alarm
            if self.sound:
                self.sound.play()
        
        # Show Popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f"Time for your {meal_name} medication!", font_size=20))
        
        btn = Button(text="Dismiss", size_hint_y=None, height=50)
        content.add_widget(btn)
        
        popup = Popup(title=f"Medication Alert: {meal_name}",
                      content=content,
                      size_hint=(None, None), size=(400, 200))
        
        btn.bind(on_press=popup.dismiss)
        popup.open()
