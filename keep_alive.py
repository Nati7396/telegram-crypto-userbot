"""
keep_alive.py
─────────────
Starts a tiny Flask web server so Replit's "Always On" / UptimeRobot pings
keep the process alive. Without this the Replit container sleeps after ~30
minutes of inactivity.
"""

from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home():
    """Simple health-check endpoint."""
    return "Telegram Userbot is alive and running!", 200


def run():
    """Run Flask on port 8080 (Replit exposes this automatically)."""
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    """Spawn the Flask server in a background daemon thread."""
    t = Thread(target=run, daemon=True)
    t.start()
    print("[keep_alive] Flask ping server started on port 8080")
