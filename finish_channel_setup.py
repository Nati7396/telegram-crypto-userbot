"""
finish_channel_setup.py
────────────────────────
Completes the channel setup that was interrupted by a flood wait:
  - Sets the profile photo
  - Posts + pins the welcome message

Run once after the flood wait clears:
    cd telegram-userbot && python finish_channel_setup.py
"""

import asyncio
import os
import struct
import zlib
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import EditPhotoRequest
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import InputChatUploadedPhoto

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

AFFILIATE_LINK  = "https://stake.com/?c=Natal"
SITE_LINK       = "https://stakecruncher.com"
CHANNEL_ID_FILE = "channel_id.txt"

WELCOME_MSG = f"""🎰 Welcome to Stake Free Coins & Rain Alerts!

We post live alerts every time free crypto is being given away in Stake.com Telegram groups — rain, tips, airdrops, draws.

🔔 Turn on notifications so you never miss a drop!

📊 Stake calculators & tools:
👉 {SITE_LINK}

🎁 New to Stake? Get a bonus:
👉 {AFFILIATE_LINK}

Stay tuned — grabs posted here in real time! 💰"""


def make_png(w, h, r, g, b):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    row  = bytes([0] + [r, g, b] * w)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b"")


async def main():
    if not os.path.exists(CHANNEL_ID_FILE):
        print("❌ channel_id.txt not found.")
        return

    channel_id = int(open(CHANNEL_ID_FILE).read().strip())
    print(f"📢 Finishing setup for channel ID: {channel_id}")

    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in.")
        return

    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})\n")

    channel = await client.get_entity(channel_id)

    # ── 1. Set profile photo ──────────────────────────────────────────────
    print("🎨 Setting channel photo …")
    try:
        with open("chan_photo.png", "wb") as f:
            f.write(make_png(512, 512, 9, 10, 14))
        uploaded = await client.upload_file("chan_photo.png")
        await client(EditPhotoRequest(channel=channel, photo=InputChatUploadedPhoto(uploaded)))
        os.remove("chan_photo.png")
        print("  ✅ Photo set!")
    except Exception as e:
        print(f"  ⚠️  Photo failed: {e}")

    await asyncio.sleep(3)

    # ── 2. Post + pin welcome message ─────────────────────────────────────
    print("📌 Posting & pinning welcome message …")
    try:
        msg = await client.send_message(channel, WELCOME_MSG, link_preview=False)
        await client(UpdatePinnedMessageRequest(peer=channel, id=msg.id, silent=True))
        print("  ✅ Welcome message pinned!")
    except Exception as e:
        print(f"  ⚠️  Message failed: {e}")

    print(f"\n✅ Channel setup complete!")
    print(f"   Channel ID: {channel_id}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
