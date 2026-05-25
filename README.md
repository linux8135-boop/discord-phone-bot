# Discord Phone Bot

Remote-control an Android device from Discord.

## How to use

1. **Create a Discord bot** at https://discord.com/developers/applications
   - New Application → Bot → Reset Token → Copy the token
   - Enable **Message Content Intent** under Bot settings
   - Invite the bot to a server with `bot` scope + `Send Messages` + `Read Message History` permissions

2. **Install the APK** on the target Android device
   - Download from GitHub Actions artifacts
   - Enable "Install from unknown sources" in Settings
   - Open the app, paste your bot token, tap START

3. **Send commands from any Discord channel the bot can see**

## Commands

| Command | Description |
|---------|-------------|
| `!ping` | Check bot is alive |
| `!shell <cmd>` | Run any shell command |
| `!screenshot` | Take a screenshot |
| `!battery` | Show battery status |
| `!photo` | Take a camera photo (needs Termux:API) |
| `!file <path>` | Upload a file |
| `!ls <path>` | List directory |
| `!cat <path>` | Read a text file |
| `!clipboard` | Read clipboard |
| `!notification <text>` | Send notification to device |
| `!device` | Show device hardware info |
| `!network` | Show network info |
| `!cpu` / `!memory` / `!disk` | System info |
| `!processes` | List running processes |

## Building yourself

Push to GitHub → GitHub Actions builds the APK automatically.
Download from the Actions tab → Artifacts.
