from gtts import gTTS
import os
import threading
# Using playsound might be tricky on some systems, let's try a simple approach or use a different lib if needed.
# For now, we'll try to use os.system or a cross-platform player if available.
# Actually, Kivy has audio capabilities, but for simple TTS playback, saving to file and playing is common.
from kivy.core.audio import SoundLoader

def play_welcome_message(username):
    """
    Generates and plays a welcome message for the user.
    """
    text = f"Welcome to Rx Shield, {username}. Your personal prescription assistant."
    
    def _generate_and_play():
        try:
            tts = gTTS(text=text, lang='en')
            filename = "welcome.mp3"
            tts.save(filename)
            
            sound = SoundLoader.load(filename)
            if sound:
                sound.play()
        except Exception as e:
            print(f"TTS Error: {e}")

    # Run in a separate thread to avoid blocking UI
    threading.Thread(target=_generate_and_play).start()

def speak_text(text):
    def _generate_and_play():
        try:
            import time
            timestamp = int(time.time() * 1000)
            filename = f"tts_{timestamp}.mp3"
            
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
            
            sound = SoundLoader.load(filename)
            if sound:
                sound.play()
                # Schedule cleanup after playing? 
                # On Windows, we can't easily delete while playing.
                # We could run a cleanup task on startup or periodic.
                # For now, let's leave them or try to delete old ones.
        except Exception as e:
            print(f"TTS Error: {e}")

    threading.Thread(target=_generate_and_play).start()
