"""
Android background service — polls SMS for activation keyword, starts Discord bot.
"""
import time
import threading
import asyncio

# ─── Configuration ──────────────────────────────────────────────
INIT_KEYWORD = "!init"
SMS_POLL_INTERVAL = 15  # seconds between SMS checks

# ─── Try Android imports (available inside p4a build) ───────────
try:
    from jnius import autoclass
    from android import AndroidService
    ANDROID = True
except ImportError:
    ANDROID = False

# ─── Globals ────────────────────────────────────────────────────
_service_running = True
_activated = False
_bot_thread = None


def get_token_from_sms():
    """Query SMS inbox via Android ContentProvider for init message."""
    if not ANDROID:
        return None
    
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        ctx = PythonActivity.mActivity
        resolver = ctx.getContentResolver()
        Uri = autoclass('android.net.Uri')
        
        cursor = resolver.query(
            Uri.parse("content://sms/inbox"),
            None, "body IS NOT NULL", None, "date DESC LIMIT 60"
        )
        
        if cursor and cursor.moveToFirst():
            body_idx = cursor.getColumnIndex("body")
            
            for _ in range(60):
                body = cursor.getString(body_idx) if body_idx >= 0 else ""
                
                if body and body.strip().lower().startswith(INIT_KEYWORD):
                    parts = body.strip().split(None, 1)
                    if len(parts) >= 2:
                        cursor.close()
                        return parts[1].strip()
                
                if not cursor.moveToNext():
                    break
            cursor.close()
    except Exception as e:
        print(f"[SMS] Query error: {e}")
    
    return None


def start_discord_bot(token):
    """Start the Discord bot with the given token."""
    global _activated, _bot_thread
    
    if _activated:
        return
    
    _activated = True
    import bot
    bot.save_token(token)
    
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot.start_bot(token))
        except Exception as e:
            print(f"[BOT] Error: {e}")
        finally:
            loop.close()
    
    _bot_thread = threading.Thread(target=run, daemon=True)
    _bot_thread.start()


def check_token_file():
    """Also check for token file on device."""
    import bot
    token = bot.load_token()
    if token:
        print("[SERVICE] Found existing token file. Connecting...")
        start_discord_bot(token)
        return True
    return False


def main():
    """Main service loop."""
    print("[SERVICE] Starting...")
    
    # Check for existing token first
    check_token_file()
    
    # Try to show notification (optional wrapper)
    try:
        if ANDROID:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            ctx = PythonActivity.mActivity
            Notification = autoclass('android.app.Notification$Builder')
            ctx_serv = ctx.getSystemService("notification")
            if hasattr(ctx, 'getString'):
                pass  # Notification support is best-effort
    except:
        pass
    
    print("[SERVICE] Polling SMS every {}s for activation: Send \"{} <TOKEN>\" to this phone".format(
        SMS_POLL_INTERVAL, INIT_KEYWORD))
    
    poll = 0
    while _service_running and not _activated:
        try:
            token = get_token_from_sms()
            if token:
                print("[SERVICE] Activation SMS received!")
                start_discord_bot(token)
                break
            
            poll += 1
            if poll % 4 == 0:
                print(f"[SERVICE] SMS poll #{poll}")
            
            time.sleep(SMS_POLL_INTERVAL)
        except Exception as e:
            print(f"[SERVICE] Error: {e}")
            time.sleep(5)
    
    print("[SERVICE] Activated. Keeping alive for bot...")
    while _service_running:
        if _bot_thread and not _bot_thread.is_alive():
            print("[SERVICE] Bot stopped. Exiting.")
            break
        time.sleep(10)
    
    print("[SERVICE] Exited.")


if __name__ == "__main__":
    main()
