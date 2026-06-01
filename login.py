"""
login.py – One-time Telegram login
────────────────────────────────────
Run this ONCE to authenticate your account and save the session file.
After this, main.py will log in automatically with no code needed.

Usage:
    cd telegram-userbot
    python login.py
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE    = os.environ["TELEGRAM_PHONE"]

async def main():
    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    me = await client.get_me()
    print(f"\n✅ Login successful!")
    print(f"   Logged in as: {me.first_name} (@{me.username})")
    print(f"   Session saved to: userbot_session.session")
    print(f"\n   You can now run: python main.py")
    await client.disconnect()

asyncio.run(main())
