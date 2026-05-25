"""
Command handlers for the Discord Phone Bot.
Each handler takes (args: str, message) and returns str or a FILE/IMAGE tuple.
"""
import os
import subprocess
import tempfile
import time
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
SHELL_TIMEOUT = 30  # seconds
MAX_OUTPUT_LINES = 80
ALLOWED_PATHS = ["/sdcard", "/storage", "/data/data/com.termux"]
HOME_DIR = str(Path.home())


# ─── Helpers ─────────────────────────────────────────────────────────────────

def run_shell(cmd, timeout=SHELL_TIMEOUT):
    """Run a shell command and return (stdout, stderr, exit_code)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout}s", -1
    except Exception as e:
        return "", str(e), -1


def trim_output(text, max_lines=MAX_OUTPUT_LINES):
    """Trim output to max_lines, appending a note if truncated."""
    lines = text.rstrip().split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (truncated {len(lines) - max_lines} more lines)"]
    return "\n".join(lines)


def safe_path(path):
    """Resolve a path, ensuring it doesn't escape allowed dirs."""
    if not path or path.startswith("~"):
        path = path.replace("~", HOME_DIR, 1)
    resolved = os.path.abspath(os.path.expanduser(path))
    # If not absolute, resolve relative to HOME
    if not os.path.isabs(resolved):
        resolved = os.path.join(HOME_DIR, resolved)
    return resolved


def format_size(size_bytes):
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ─── Commands ────────────────────────────────────────────────────────────────

async def cmd_ping(args, message):
    """Check if the bot is alive."""
    return f"Pong! Latency: {round(message.created_at.timestamp() * 1000)}ms"


async def cmd_help(args, message):
    """Show available commands."""
    return """**Discord Phone Bot Commands**

**Core**
• `!ping` — Check if bot is alive
• `!help` — Show this help

**Shell & System**
• `!shell <cmd>` — Run any shell command
• `!battery` — Show battery status
• `!screenshot` — Take a screenshot
• `!clipboard` — Read clipboard content
• `!notification <text>` — Send a notification to this device

**Files**
• `!ls <path>` — List directory contents
• `!cat <path>` — Read a text file
• `!file <path>` — Upload a file to Discord
• `!info <path>` — Show file/directory info
• `!disk` — Show storage usage

**Device Info**
• `!device` — Show device hardware/OS info
• `!processes` — List running processes
• `!network` — Show network info (IP, interfaces)
• `!cpu` — Show CPU info & load
• `!memory` — Show RAM usage

For detailed help on a command: `!help <command>`"""


async def cmd_shell(args, message):
    """Run an arbitrary shell command."""
    if not args:
        return "Usage: `!shell <command>`"
    out, err, code = run_shell(args)
    result = ""
    if out:
        result += trim_output(out)
    if err:
        result += f"\n[STDERR]\n{trim_output(err)}"
    result += f"\n\nExit code: {code}"
    return result.strip()


async def cmd_battery(args, message):
    """Show battery info via Android dumpsys."""
    out, err, code = run_shell("dumpsys battery 2>/dev/null || echo 'ERROR: no dumpsys'")
    if "ERROR" in out:
        return "Battery info not available (needs Android debug access)."
    # Parse useful fields
    lines = out.strip().split("\n")
    parsed = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip()] = v.strip()
    ac = parsed.get("AC powered", "?")
    usb = parsed.get("USB powered", "?")
    level = parsed.get("level", "?")
    scale = parsed.get("scale", "100")
    status_map = {"1": "Unknown", "2": "Charging", "3": "Discharging",
                  "4": "Not charging", "5": "Full"}
    status = status_map.get(parsed.get("status", "?"), "?")
    temp_raw = parsed.get("temperature", "0")
    try:
        temp = f"{int(temp_raw) / 10:.1f}°C"
    except:
        temp = "?"
    voltage_raw = parsed.get("voltage", "0")
    try:
        voltage = f"{int(voltage_raw) / 1000:.3f}V"
    except:
        voltage = "?"
    tech = parsed.get("technology", "?")
    pct = f"{level}/{scale}" if level != "?" else "?"
    return (
        f"**Battery**\n"
        f"Level: {pct}%\n"
        f"Status: {status}\n"
        f"Powered: AC={ac} USB={usb}\n"
        f"Temp: {temp}\n"
        f"Voltage: {voltage}\n"
        f"Technology: {tech}"
    )


async def cmd_screenshot(args, message):
    """Take a screenshot using Android's built-in screencap."""
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp_path = tmp.name
    tmp.close()
    out, err, code = run_shell(f"/system/bin/screencap -p '{tmp_path}'")
    if code != 0 or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        return f"Screenshot failed: {err or 'unknown error'}"
    os.chmod(tmp_path, 0o644)
    return ("IMAGE", tmp_path, "Screenshot captured!")


async def cmd_clipboard(args, message):
    """Read the Android clipboard."""
    out, err, code = run_shell("termux-clipboard-get 2>/dev/null")
    if out.strip():
        return f"**Clipboard:**\n{out.strip()}"
    # Fallback
    out2, err2, code2 = run_shell(
        "dumpsys clipboard 2>/dev/null | grep -i 'text' | head -5"
    )
    if out2.strip():
        return f"**Clipboard:**\n{out2.strip()}"
    return "Clipboard empty or inaccessible."


async def cmd_notification(args, message):
    """Send a notification to the device."""
    if not args:
        return "Usage: `!notification <text>`"
    # Try termux-notification first
    out, err, code = run_shell(
        f"termux-notification --title 'Discord Bot' --content '{args}' --id dcb_1 2>/dev/null"
    )
    if code == 0:
        return f"Notification sent: {args}"
    return f"Notification failed (install Termux:API?): {err}"


async def cmd_ls(args, message):
    """List directory contents."""
    path = safe_path(args if args else ".")
    if not os.path.exists(path):
        return f"Path not found: {path}"
    if not os.path.isdir(path):
        return f"Not a directory: {path}"
    try:
        items = os.listdir(path)
    except PermissionError:
        return f"Permission denied: {path}"
    items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    lines = []
    for name in items:
        full = os.path.join(path, name)
        try:
            stat = os.stat(full)
            size = format_size(stat.st_size) if os.path.isfile(full) else ""
            modified = time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime))
            dtype = "📁" if os.path.isdir(full) else "📄"
            lines.append(f"{dtype} {name:<30} {size:>8}  {modified}")
        except:
            lines.append(f"  {name}")
    header = f"**{path}/** — {len(items)} items\n"
    return header + "```\n" + "\n".join(lines[:60]) + "```"


async def cmd_cat(args, message):
    """Read a text file."""
    if not args:
        return "Usage: `!cat <path>`"
    path = safe_path(args)
    if not os.path.exists(path):
        return f"File not found: {path}"
    if not os.path.isfile(path):
        return f"Not a file: {path}"
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read(10000)  # Max 10k chars
    except PermissionError:
        return f"Permission denied: {path}"
    except Exception as e:
        return f"Error reading file: {e}"
    return f"**{path}**\n```\n{content}\n```" if content.strip() else "(empty file)"


async def cmd_file(args, message):
    """Upload a file to Discord."""
    if not args:
        return "Usage: `!file <path>`"
    path = safe_path(args)
    if not os.path.exists(path):
        return f"File not found: {path}"
    if not os.path.isfile(path):
        return f"Not a file: {path}"
    size = os.path.getsize(path)
    # Discord file limit is 25MB for most servers; 100MB for boosted
    if size > 25 * 1024 * 1024:
        return f"File too large ({format_size(size)}). Max 25MB."
    fname = os.path.basename(path)
    return ("FILE", path, f"**{fname}** ({format_size(size)})")


async def cmd_info(args, message):
    """Show file/directory info."""
    path = safe_path(args if args else ".")
    if not os.path.exists(path):
        return f"Path not found: {path}"
    stat = os.stat(path)
    lines = [f"**{os.path.basename(path)}**"]
    lines.append(f"Full path: `{os.path.abspath(path)}`")
    lines.append(f"Type: {'Directory' if os.path.isdir(path) else 'File'}")
    lines.append(f"Size: {format_size(stat.st_size)}")
    lines.append(f"Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))}")
    lines.append(f"Permissions: {oct(stat.st_mode & 0o777)}")
    return "\n".join(lines)


async def cmd_disk(args, message):
    """Show storage usage."""
    out, err, code = run_shell("df -h /data /sdcard /storage 2>/dev/null || df -h / 2>/dev/null")
    return f"**Storage**\n```\n{out.strip()}\n```"


async def cmd_device(args, message):
    """Show device hardware and OS info."""
    props = {}
    for prop in ["ro.product.model", "ro.product.manufacturer", "ro.build.version.release",
                  "ro.build.version.sdk", "ro.serialno"]:
        o, _, _ = run_shell(f"getprop {prop} 2>/dev/null")
        props[prop] = o.strip() or "?"
    out, _, _ = run_shell("uname -a")
    return (
        f"**Device Info**\n"
        f"Model: {props['ro.product.model']}\n"
        f"Manufacturer: {props['ro.product.manufacturer']}\n"
        f"Android: {props['ro.build.version.release']} (SDK {props['ro.build.version.sdk']})\n"
        f"Serial: {props['ro.serialno']}\n"
        f"Kernel: `{out.strip()}`"
    )


async def cmd_processes(args, message):
    """List running processes."""
    out, err, code = run_shell("ps -A -o PID,USER,NAME 2>/dev/null | head -60 || ps 2>/dev/null | head -60")
    return f"**Processes**\n```\n{out.strip()}\n```"


async def cmd_network(args, message):
    """Show network info."""
    lines = []
    ip_out, _, _ = run_shell("ip -4 addr show 2>/dev/null | grep inet || ifconfig 2>/dev/null")
    lines.append(f"**IPs**\n```\n{ip_out.strip()[:1000]}\n```")
    wifi_out, _, _ = run_shell(
        "dumpsys wifi 2>/dev/null | grep 'mWifiInfo' | head -3 || echo 'WiFi info unavailable'"
    )
    lines.append(f"**WiFi**\n`{wifi_out.strip()[:300]}`")
    return "\n".join(lines)


async def cmd_cpu(args, message):
    """Show CPU info and load."""
    out1, _, _ = run_shell("cat /proc/cpuinfo 2>/dev/null | head -20")
    out2, _, _ = run_shell("cat /proc/loadavg 2>/dev/null")
    out3, _, _ = run_shell("uptime 2>/dev/null")
    return f"**CPU**\n```\n{out1.strip()}\n```\n**Load:** `{out2.strip()}`\n**Uptime:** `{out3.strip()}`"


async def cmd_memory(args, message):
    """Show RAM usage."""
    out, _, _ = run_shell("cat /proc/meminfo 2>/dev/null | grep -E '^(MemTotal|MemFree|MemAvailable|Swap)' | head -10")
    return f"**Memory**\n```\n{out.strip()}\n```"


async def cmd_photo(args, message):
    """Take a photo using the camera (requires Termux:API)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp_path = tmp.name
    tmp.close()
    out, err, code = run_shell(f"termux-camera-photo '{tmp_path}' 2>/dev/null")
    if code != 0 or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        return f"Camera failed (install Termux:API?): {err or 'no image captured'}"
    os.chmod(tmp_path, 0o644)
    return ("IMAGE", tmp_path, "Photo captured!")


# ─── Command Registry ────────────────────────────────────────────────────────

COMMANDS = {
    "ping": cmd_ping,
    "help": cmd_help,
    "shell": cmd_shell,
    "sh": cmd_shell,
    "bash": cmd_shell,
    "battery": cmd_battery,
    "bat": cmd_battery,
    "screenshot": cmd_screenshot,
    "sc": cmd_screenshot,
    "screen": cmd_screenshot,
    "clipboard": cmd_clipboard,
    "clip": cmd_clipboard,
    "notification": cmd_notification,
    "notify": cmd_notification,
    "ls": cmd_ls,
    "dir": cmd_ls,
    "cat": cmd_cat,
    "file": cmd_file,
    "upload": cmd_file,
    "info": cmd_info,
    "stat": cmd_info,
    "disk": cmd_disk,
    "df": cmd_disk,
    "device": cmd_device,
    "phone": cmd_device,
    "processes": cmd_processes,
    "ps": cmd_processes,
    "network": cmd_network,
    "net": cmd_network,
    "wifi": cmd_network,
    "cpu": cmd_cpu,
    "memory": cmd_memory,
    "mem": cmd_memory,
    "ram": cmd_memory,
    "photo": cmd_photo,
    "camera": cmd_photo,
}


async def handle_command(cmd_name, args, message):
    """Route a command to its handler."""
    handler = COMMANDS.get(cmd_name)
    if handler is None:
        return f"Unknown command: `{cmd_name}`. Try `!help`."
    return await handler(args, message)
