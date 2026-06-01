"""
create_groups.py
────────────────
Creates 100 Telegram supergroups:
  - Named by their own Telegram group ID
  - Chat history visible to new members
  - A welcome message sent in each
  - Safe delays to avoid Telegram flood bans
"""

import asyncio
import os
import random
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditTitleRequest,
    TogglePreHistoryHiddenRequest,
)
from telethon.errors import FloodWaitError, ChatNotModifiedError

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

TOTAL_GROUPS = 100

# Message sent in every newly created group
WELCOME_MESSAGE = (
    "👋 Hello! This group is active and ready.\n"
    "Join us and stay tuned for updates!"
)


async def main():
    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in. Run: python do_login.py --request")
        return

    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name} (@{me.username})")
    print(f"📦 Creating {TOTAL_GROUPS} supergroups …\n")

    created = []
    failed  = []
    n = 0

    while n < TOTAL_GROUPS:
        attempt_num = n + 1
        try:
            # ── 1. Create supergroup (megagroup=True) ──────────────────────
            result = await client(CreateChannelRequest(
                title=f"Group {attempt_num}",  # temp title, will rename below
                about="",
                megagroup=True,                # supergroup, not a channel
            ))
            channel  = result.chats[0]
            group_id = channel.id

            # ── 2. Rename to its own Telegram ID ──────────────────────────
            await client(EditTitleRequest(channel=channel, title=str(group_id)))

            # ── 3. Make chat history visible to new members ───────────────
            #    enabled=False  → history IS visible (toggle "hidden" off)
            #    Silently skip if already in the correct state
            try:
                await client(TogglePreHistoryHiddenRequest(channel=channel, enabled=False))
            except ChatNotModifiedError:
                pass  # already visible — no action needed

            # ── 4. Send welcome message ───────────────────────────────────
            await client.send_message(channel, WELCOME_MESSAGE)

            n += 1
            created.append(group_id)
            print(f"  [{n:>3}/{TOTAL_GROUPS}] ✅ Created supergroup ID={group_id}")

            # Safe random delay between each group
            delay = random.uniform(4, 8)
            await asyncio.sleep(delay)

        except FloodWaitError as e:
            print(f"  ⏳ Telegram flood wait: sleeping {e.seconds}s …")
            await asyncio.sleep(e.seconds + 2)
            # Do NOT increment n — retry same group

        except Exception as e:
            print(f"  ❌ Error on group {attempt_num}: {e}")
            failed.append(attempt_num)
            n += 1  # skip and move on
            await asyncio.sleep(5)

    print(f"\n{'='*50}")
    print(f"✅ Created:  {len(created)}")
    print(f"❌ Failed:   {len(failed)}")
    if failed:
        print(f"   Failed at: {failed}")
    print(f"{'='*50}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
