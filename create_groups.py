"""
create_groups.py
────────────────
Creates 100 Telegram supergroups:
  - Named by their own Telegram group ID
  - Profile photo set
  - Chat history visible to new members
  - A welcome message sent in each
  - Longer safe delays to avoid flood bans
"""

import asyncio
import os
import random
import struct
import zlib
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditTitleRequest,
    EditPhotoRequest,
    TogglePreHistoryHiddenRequest,
)
from telethon.tl.types import InputChatUploadedPhoto
from telethon.errors import FloodWaitError, ChatNotModifiedError

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

TOTAL_GROUPS = 100
PHOTO_FILE   = "group_photo.png"

# Message sent in every newly created group
WELCOME_MESSAGE = (
    "👋 Hello! This group is active and ready.\n"
    "Stay tuned for updates and giveaways!"
)


def make_png(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Generate a solid-color PNG using only built-in Python modules."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row       = bytes([0] + [r, g, b] * width)
    idat_data = zlib.compress(row * height)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr_data)
        + chunk(b"IDAT", idat_data)
        + chunk(b"IEND", b"")
    )


async def set_photo(client, channel, uploaded_photo):
    """Set the profile photo for a channel/supergroup."""
    try:
        await client(EditPhotoRequest(
            channel=channel,
            photo=InputChatUploadedPhoto(uploaded_photo)
        ))
    except Exception as e:
        print(f"  ⚠️  Photo set failed: {e}")


async def main():
    # ── Generate group photo (dark navy blue, 512×512) ────────────────────
    print("🎨 Generating group profile photo …")
    try:
        with open(PHOTO_FILE, "wb") as f:
            f.write(make_png(512, 512, 26, 31, 54))   # dark navy #1a1f36
        print(f"  ✅ Photo ready: {PHOTO_FILE}")
        PHOTO_FILE_READY = True
    except Exception as e:
        print(f"  ⚠️  Could not generate photo: {e}")
        PHOTO_FILE_READY = False

    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in. Run: python do_login.py --request")
        return

    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})")
    print(f"📦 Creating {TOTAL_GROUPS} supergroups …\n")

    # Upload the photo file once (reused for every group)
    uploaded_photo = None
    if PHOTO_FILE_READY:
        try:
            uploaded_photo = await client.upload_file(PHOTO_FILE)
            print("  📤 Photo uploaded to Telegram\n")
        except Exception as e:
            print(f"  ⚠️  Photo upload failed: {e}\n")

    created = []
    failed  = []
    n = 0

    while n < TOTAL_GROUPS:
        attempt_num = n + 1
        try:
            # 1. Create supergroup
            result = await client(CreateChannelRequest(
                title=f"Group {attempt_num}",
                about="",
                megagroup=True,
            ))
            channel  = result.chats[0]
            group_id = channel.id

            await asyncio.sleep(2)

            # 2. Rename to its own Telegram ID
            await client(EditTitleRequest(channel=channel, title=str(group_id)))

            await asyncio.sleep(2)

            # 3. Set profile photo
            if uploaded_photo:
                await set_photo(client, channel, uploaded_photo)
                await asyncio.sleep(2)

            # 4. Make chat history visible to new members
            try:
                await client(TogglePreHistoryHiddenRequest(channel=channel, enabled=False))
            except ChatNotModifiedError:
                pass
            await asyncio.sleep(1)

            # 5. Send welcome message
            await client.send_message(channel, WELCOME_MESSAGE)

            n += 1
            created.append(group_id)
            print(f"  [{n:>3}/{TOTAL_GROUPS}] ✅ ID={group_id} — photo set, message sent")

            # Longer delay between groups to avoid flood bans (15–25s)
            delay = random.uniform(15, 25)
            print(f"           ⏱  Next in {delay:.0f}s …")
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            print(f"  ⏳ Flood wait: sleeping {e.seconds}s …")
            await asyncio.sleep(e.seconds + 5)

        except Exception as e:
            print(f"  ❌ Error on group {attempt_num}: {e}")
            failed.append(attempt_num)
            n += 1
            await asyncio.sleep(10)

    # Cleanup
    if PHOTO_FILE_READY and os.path.exists(PHOTO_FILE):
        os.remove(PHOTO_FILE)

    print(f"\n{'='*50}")
    print(f"✅ Created:  {len(created)}")
    print(f"❌ Failed:   {len(failed)}")
    print(f"{'='*50}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
