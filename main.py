"""Stealth launcher — starts foreground service and exits."""
import sys
import os

# P4A service name (matches buildozer.spec)
SERVICE_NAME = "BotService"


def start_service():
    """Start the foreground service."""
    try:
        # P4A provides the android module at runtime
        from android import AndroidService  # type: ignore
        service = AndroidService(SERVICE_NAME, "Phone bot active")
        service.start("")
    except ImportError:
        pass  # Not running on-device


start_service()
