"""
Discord Phone Bot — Kivy Android App.
Provides a simple UI to configure and control the Discord bot.
"""
import threading
import sys
import os
from io import StringIO

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

# Redirect stdout so we can capture bot logs
log_buffer = StringIO()


class LogCapture:
    def __init__(self, original, buffer):
        self.original = original
        self.buffer = buffer

    def write(self, text):
        self.original.write(text)
        self.buffer.write(text)

    def flush(self):
        self.original.flush()
        self.buffer.flush()


# Capture print statements
sys.stdout = LogCapture(sys.stdout, log_buffer)
sys.stderr = LogCapture(sys.stderr, log_buffer)


class DiscordBotApp(App):
    """Kivy application for the Discord Phone Bot."""

    def build(self):
        self.bot_thread = None
        self.running = False
        self.bot_module = None
        self.token_file = os.path.join(self.user_data_dir, "token.txt")

        Window.clearcolor = (0.12, 0.12, 0.14, 1)
        Window.size = (400, 600)

        root = BoxLayout(orientation="vertical", padding=10, spacing=8)

        # Title
        title = Label(
            text="[b]Discord Phone Bot[/b]",
            markup=True,
            size_hint_y=0.08,
            color=(0.2, 0.6, 1, 1),
            font_size=18,
        )
        root.add_widget(title)

        # Token input
        token_layout = BoxLayout(
            orientation="vertical", size_hint_y=0.12, spacing=4
        )
        token_layout.add_widget(
            Label(
                text="Bot Token (from Discord Developer Portal)",
                color=(0.8, 0.8, 0.8, 1),
                font_size=12,
                halign="left",
                size_hint_y=0.3,
            )
        )
        self.token_input = TextInput(
            hint_text="Enter your Discord bot token...",
            password=True,
            password_mask="*",
            multiline=False,
            size_hint_y=0.7,
            background_color=(0.2, 0.2, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            cursor_color=(0.2, 0.6, 1, 1),
        )
        self._load_token()
        token_layout.add_widget(self.token_input)
        root.add_widget(token_layout)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=8)
        self.start_btn = Button(
            text="START BOT",
            background_color=(0.2, 0.7, 0.3, 1),
            background_normal="",
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.start_btn.bind(on_press=self.start_bot)
        btn_layout.add_widget(self.start_btn)

        self.stop_btn = Button(
            text="STOP BOT",
            background_color=(0.7, 0.2, 0.2, 1),
            background_normal="",
            color=(1, 1, 1, 1),
            bold=True,
            disabled=True,
        )
        self.stop_btn.bind(on_press=self.stop_bot)
        btn_layout.add_widget(self.stop_btn)
        root.add_widget(btn_layout)

        # Status label
        self.status_label = Label(
            text="Ready — enter token and press START",
            size_hint_y=0.06,
            color=(0.6, 0.6, 0.6, 1),
            font_size=12,
        )
        root.add_widget(self.status_label)

        # Log output
        log_label = Label(
            text="Logs:",
            size_hint_y=0.03,
            color=(0.8, 0.8, 0.8, 1),
            font_size=11,
            halign="left",
        )
        root.add_widget(log_label)

        self.log_output = TextInput(
            readonly=True,
            text="Waiting to start...\n",
            background_color=(0.08, 0.08, 0.1, 1),
            foreground_color=(0.3, 0.9, 0.3, 1),
            font_size=10,
            size_hint_y=0.55,
        )
        scroll = ScrollView(size_hint_y=0.55)
        scroll.add_widget(self.log_output)
        root.add_widget(scroll)

        # Update log periodically
        Clock.schedule_interval(self.update_log, 0.5)

        return root

    def _load_token(self):
        """Load saved token from disk."""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    token = f.read().strip()
                    if token:
                        self.token_input.text = token
        except Exception:
            pass

    def _save_token(self):
        """Save token to disk."""
        try:
            with open(self.token_file, "w") as f:
                f.write(self.token_input.text.strip())
        except Exception:
            pass

    def update_log(self, dt):
        """Update the log display from the captured stdout buffer."""
        current = log_buffer.getvalue()
        if current:
            self.log_output.text = current[-5000:]  # Keep last 5000 chars
            self.log_output.cursor = (0, len(self.log_output.text))

    def log(self, msg):
        """Append a message to the log."""
        print(f"[APP] {msg}")

    def start_bot(self, instance):
        """Start the Discord bot in a background thread."""
        token = self.token_input.text.strip()
        if not token:
            self.status_label.text = "ERROR: Enter a bot token first!"
            return

        if self.running:
            self.status_label.text = "Bot is already running!"
            return

        self._save_token()
        self.running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.token_input.disabled = True
        self.status_label.text = "Starting bot..."

        def run_bot():
            try:
                from bot import start_bot
                self.log(f"Connecting with token: {token[:8]}...")
                start_bot(token)
            except Exception as e:
                self.log(f"Bot error: {e}")
                # Reset UI state
                Clock.schedule_once(lambda dt: self._reset_ui(), 0)
                self.running = False

        self.bot_thread = threading.Thread(target=run_bot, daemon=True)
        self.bot_thread.start()
        self.log("Bot thread launched.")
        Clock.schedule_once(lambda dt: self._set_status("Bot running!"), 2)

    def stop_bot(self, instance):
        """Stop the bot."""
        if not self.running:
            return
        self.log("Stopping bot...")
        self.status_label.text = "Stopping bot..."
        try:
            from bot import stop_bot
            stop_bot()
        except Exception as e:
            self.log(f"Stop error: {e}")
        self._reset_ui()

    def _reset_ui(self):
        self.running = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.token_input.disabled = False
        self.status_label.text = "Bot stopped."

    def _set_status(self, text):
        self.status_label.text = text

    def on_stop(self):
        """Clean up when app closes."""
        if self.running:
            try:
                from bot import stop_bot
                stop_bot()
            except Exception:
                pass


if __name__ == "__main__":
    DiscordBotApp().run()
