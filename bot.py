"""
Discord Phone Bot — Core bot logic.
Connects to Discord and handles incoming commands.
"""
import asyncio
import discord
from commands import handle_command

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

BOT_TOKEN = None
BOT_LOOP = None
CMD_PREFIX = "!"


async def send_long(destination, text, max_len=1900):
    """Split long messages into multiple Discord-safe chunks."""
    if len(text) <= max_len:
        await destination.send(f"```\n{text}\n```")
        return
    # Send header
    await destination.send(f"```\n{text[:max_len]}\n```")
    # Send remaining chunks
    remaining = text[max_len:]
    while remaining:
        chunk = remaining[:max_len]
        await destination.send(f"```\n{chunk}\n```")
        remaining = remaining[max_len:]


@client.event
async def on_ready():
    print(f"[BOT] Logged in as {client.user} (ID: {client.user.id})")
    print("[BOT] Bot is ready — listening for commands.")


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.content.startswith(CMD_PREFIX):
        return

    parts = message.content[len(CMD_PREFIX):].strip().split(maxsplit=0)
    if not parts:
        return

    raw = message.content[len(CMD_PREFIX):].strip()
    # Extract command name and args
    cmd_parts = raw.split(maxsplit=1)
    cmd_name = cmd_parts[0].lower()
    cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""

    print(f"[BOT] Command: {cmd_name} | Args: {cmd_args[:50]}")

    try:
        result = await handle_command(cmd_name, cmd_args, message)
        if result is not None:
            if isinstance(result, tuple) and result[0] == "FILE":
                _, filepath, caption = result
                await message.channel.send(
                    content=caption,
                    file=discord.File(filepath)
                )
            elif isinstance(result, tuple) and result[0] == "IMAGE":
                _, filepath, caption = result
                await message.channel.send(
                    content=caption,
                    file=discord.File(filepath)
                )
            else:
                await send_long(message.channel, str(result))
    except Exception as e:
        print(f"[BOT] Error handling command '{cmd_name}': {e}")
        await message.channel.send(f"Error: {e}")


def start_bot(token):
    """Start the Discord bot with the given token. Blocks until disconnect."""
    global BOT_TOKEN
    BOT_TOKEN = token
    client.run(token)


def stop_bot():
    """Gracefully disconnect the bot."""
    if client.is_ready():
        asyncio.run_coroutine_threadsafe(client.close(), client.loop)
        print("[BOT] Disconnected.")
