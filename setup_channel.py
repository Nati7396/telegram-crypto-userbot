"""
setup_channel.py
─────────────────
Creates your Stake.com affiliate promo channel:
  - Named "Stake Free Coins 🎰 | Rain Alerts"
  - Sets description + profile photo
  - Posts a pinned welcome message with your affiliate link
  - Saves the channel ID to channel_id.txt for the main bot to use

Run ONCE: python setup_channel.py
"""

import asyncio
import os
import struct
import zlib
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditPhotoRequest,
    EditTitleRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import InputChatUploadedPhoto
from telethon.errors import ChatNotModifiedError

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

AFFILIATE_LINK = "https://stake.com/?c=Natal"
CHANNEL_ID_FILE = "channel_id.txt"

CHANNEL_NAME = "Stake Free Coins 🎰 | Rain Alerts"
CHANNEL_DESC = (
    "🚨 Live rain, tip & airdrop alerts from Stake.com groups.\n"
    "✅ Grab free crypto every day!\n\n"
    "📊 Tools & calculators: https://stakecruncher.com\n"
    f"🎁 Get free Stake balance: {AFFILIATE_LINK}"
)

WELCOME_MSG = f"""🎰 Welcome to Stake Free Coins & Rain Alerts!

We post live alerts every time free crypto is being given away in Stake.com Telegram groups — rain, tips, airdrops, draws.

🔔 Turn on notifications so you never miss a drop!

📊 Stake calculators & tools:
👉 https://stakecruncher.com

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
    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in. Run: python do_login.py --request")
        return

    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})\n")

    # ── 1. Create the channel ─────────────────────────────────────────────
    print("📢 Creating promo channel …")
    result = await client(CreateChannelRequest(
        title=CHANNEL_NAME,
        about=CHANNEL_DESC,
        broadcast=True,    # channel (broadcast), not a group
        megagroup=False,
    ))
    channel = result.chats[0]
    cid = channel.id
    print(f"  ✅ Channel created: ID={cid}")

    await asyncio.sleep(2)

    # ── 2. Set profile photo ──────────────────────────────────────────────
    print("🎨 Setting channel photo …")
    with open("chan_photo.png", "wb") as f:
        f.write(make_png(512, 512, 9, 10, 14))   # #090A0E — matches StakeCruncher dark theme
    uploaded = await client.upload_file("chan_photo.png")
    await client(EditPhotoRequest(channel=channel, photo=InputChatUploadedPhoto(uploaded)))
    os.remove("chan_photo.png")
    print("  ✅ Photo set")

    await asyncio.sleep(2)

    # ── 3. Post + pin welcome message ─────────────────────────────────────
    print("📌 Posting & pinning welcome message …")
    msg = await client.send_message(channel, WELCOME_MSG, link_preview=False)
    await client(UpdatePinnedMessageRequest(peer=channel, id=msg.id, silent=True))
    print("  ✅ Welcome message pinned")

    # ── 4. Save channel ID for main bot ──────────────────────────────────
    with open(CHANNEL_ID_FILE, "w") as f:
        f.write(str(cid))
    print(f"\n✅ All done! Channel ID saved to {CHANNEL_ID_FILE}")
    print(f"   The main bot will auto-post grabs to this channel.")
    print(f"\n   Share your channel link:")
    print(f"   https://t.me/{getattr(channel, 'username', None) or 'your_channel'}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
