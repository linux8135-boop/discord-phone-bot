"""Android foreground service — keeps bot alive."""
import asyncio
import sys
import os

# Python-for-Android service bootstrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bot as _bot


def start():
    """Entry point called by PythonService on Android."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_bot.start_bot())
    except Exception:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    start()
