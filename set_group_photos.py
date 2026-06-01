"""
set_group_photos.py
────────────────────
Sets a profile photo on all groups you own that are named by numeric ID
(i.e. the ones created by create_groups.py).

Run this once after create_groups.py finishes to patch the first groups
that were created before photo support was added.
"""

import asyncio
import os
import urllib.request
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import EditPhotoRequest
from telethon.tl.types import InputChatUploadedPhoto
from telethon.errors import FloodWaitError

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

PHOTO_URL  = "https://ui-avatars.com/api/?name=G&size=512&background=1a1f36&color=00d4ff&bold=true&format=png"
PHOTO_FILE = "group_photo.png"


async def main():
    print("📥 Downloading group profile photo …")
    urllib.request.urlretrieve(PHOTO_URL, PHOTO_FILE)
    print(f"  ✅ Photo ready: {PHOTO_FILE}\n")

    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in.")
        return

    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})")

    # Find all groups/supergroups owned by us and named with a numeric ID
    targets = []
    async for dialog in client.iter_dialogs():
        title = (dialog.title or "").strip()
        if (dialog.is_group or dialog.is_channel) and title.isdigit():
            targets.append((dialog.entity, title))

    print(f"🎯 Found {len(targets)} group(s) with numeric-ID names\n")

    if not targets:
        print("Nothing to do.")
        await client.disconnect()
        return

    # Upload once, reuse for all
    uploaded = await client.upload_file(PHOTO_FILE)
    print("📤 Photo uploaded to Telegram\n")

    done = 0
    for entity, title in targets:
        try:
            await client(EditPhotoRequest(
                channel=entity,
                photo=InputChatUploadedPhoto(uploaded)
            ))
            print(f"  ✅ Set photo for group {title}")
            done += 1
            await asyncio.sleep(3)
        except FloodWaitError as e:
            print(f"  ⏳ Flood wait {e.seconds}s …")
            await asyncio.sleep(e.seconds + 2)
            # retry
            try:
                await client(EditPhotoRequest(channel=entity, photo=InputChatUploadedPhoto(uploaded)))
                print(f"  ✅ Set photo for group {title} (retry)")
                done += 1
            except Exception as e2:
                print(f"  ❌ Still failed: {e2}")
        except Exception as e:
            print(f"  ⚠️  Failed for {title}: {e}")

    if os.path.exists(PHOTO_FILE):
        os.remove(PHOTO_FILE)

    print(f"\n✅ Done! Photo set for {done}/{len(targets)} groups.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
