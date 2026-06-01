"""
main.py – Telegram Userbot (Telethon) — @cctip_bot / Cwallet grabber
──────────────────────────────────────────────────────────────────────
Strategy:
  1. Scan ALL groups you are already in and find the ones where @cctip_bot
     is a member — those are the real giveaway groups.
  2. Also watch a seed list of known @cctip_bot / Cwallet groups and join them.
  3. Listen ONLY for messages FROM @cctip_bot (uid 1559503444) or @Cwallet_com_Bot
     that announce /airdrop /rain /draw /giveaway /lucky.
  4. Auto-grab: click "Grab a Share" / "Grab" buttons, reply with the grab
     keyword, send commands to @cctip_bot in that group.
  5. Notify Saved Messages + console every time something is grabbed.

Requirements: telethon, flask, python-dotenv
"""

import asyncio
import os
import random
import re
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import (
    ChatWriteForbiddenError,
    FloodWaitError,
    UserAlreadyParticipantError,
    ChannelPrivateError,
)
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
from telethon.tl.types import ChannelParticipant

from keep_alive import keep_alive

# ─── Env ─────────────────────────────────────────────────────────────────────
load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE    = os.environ["TELEGRAM_PHONE"]

SESSION_NAME = "userbot_session"

# ─── @cctip_bot / @Cwallet_com_Bot identifiers ───────────────────────────────
# These are the ONLY bots whose messages we act on.
CCTIP_USERNAMES = {"cctip_bot", "cwallet_com_bot", "cctipcoin_bot"}

# ─── Giveaway command keywords (must appear in the bot's message) ─────────────
GIVEAWAY_PATTERN = re.compile(
    r"/airdrop|/rain|/draw|/giveaway|/lucky|/tip\b|grab a share|airdrop started|rain started|giveaway started",
    re.IGNORECASE,
)

# ─── Buttons we click ────────────────────────────────────────────────────────
GRAB_BUTTON_LABELS = {
    "grab", "grab a share", "claim", "join", "participate",
    "get", "claim reward", "take", "join airdrop",
}

# ─── Keyword to type in chat when no button is found ─────────────────────────
GRAB_KEYWORD = "grab"

# ─── Seed list of known real @cctip_bot / Cwallet groups to join at start ────
# These are actual Cwallet / CCTip community groups.
SEED_GROUPS = [
    "Cwallet_official",       # Cwallet official community
    "cctip_official",         # CCTip official
    "cwallet_announcements",  # Announcements
    "CwalletGlobal",
    "CCTipCommunity",
    "cctip_rain",
    "cwallet_rain",
    "CryptoRainOfficial",
    "RainCrypto",
    "CCTipAirdrop",
    "CwalletAirdrop",
    "TipBotCrypto",
    "CryptoTipRain",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


async def safe_delay(min_s=2.0, max_s=5.0):
    d = random.uniform(min_s, max_s)
    await asyncio.sleep(d)


async def notify_self(client, text):
    try:
        await client.send_message("me", text)
    except Exception as e:
        log(f"  [notify] {e}")


async def join_group(client, entity):
    try:
        await client(JoinChannelRequest(entity))
        log(f"  ✅ Joined: {getattr(entity, 'title', entity)}")
    except UserAlreadyParticipantError:
        pass
    except FloodWaitError as e:
        log(f"  ⏳ Flood wait {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        log(f"  ⚠️  Could not join: {e}")


async def cctip_bot_in_group(client, group) -> bool:
    """Return True if @cctip_bot or @Cwallet_com_Bot is a member of this group."""
    for uname in CCTIP_USERNAMES:
        try:
            await client(GetParticipantRequest(group, uname))
            return True
        except Exception:
            continue
    return False


async def scan_my_groups(client):
    """
    Scan all dialogs the account is in.
    Return list of (entity, title) where @cctip_bot is a member.
    """
    found = []
    log("🔍 Scanning your groups for @cctip_bot presence …")
    async for dialog in client.iter_dialogs():
        if not dialog.is_group and not dialog.is_channel:
            continue
        try:
            if await cctip_bot_in_group(client, dialog.entity):
                found.append(dialog.entity)
                log(f"  ✅ @cctip_bot found in: {dialog.title}")
                await asyncio.sleep(0.5)
        except Exception:
            continue
    return found


async def try_click_buttons(message) -> bool:
    if not message.reply_markup:
        return False
    clicked = False
    rows = getattr(message.reply_markup, "rows", [])
    for row in rows:
        for button in row.buttons:
            label = getattr(button, "text", "").strip().lower()
            if label in GRAB_BUTTON_LABELS:
                try:
                    await message.click(data=button.data)
                    log(f"  🖱️  Clicked: '{button.text}'")
                    clicked = True
                    await safe_delay(1, 2)
                except Exception as e:
                    log(f"  ⚠️  Click failed: {e}")
    return clicked


async def grab_giveaway(client, chat, message, giveaway_type: str):
    """
    Full grab sequence for a detected @cctip_bot giveaway.
    """
    chat_title = getattr(chat, "title", None) or str(chat.id)
    log(f"🎯 GRAB triggered in [{chat_title}] — type: {giveaway_type}")

    await safe_delay(1, 3)

    # 1. Click inline button (Grab a Share / Grab / Claim)
    clicked = await try_click_buttons(message)

    await safe_delay(1, 2)

    # 2. Reply with grab keyword to the bot's message
    try:
        await message.reply(GRAB_KEYWORD)
        log(f"  📩 Replied '{GRAB_KEYWORD}'")
    except ChatWriteForbiddenError:
        log("  ⚠️  Can't write in this group")
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception as e:
        log(f"  ⚠️  Reply failed: {e}")

    await safe_delay(1, 2)

    # 3. Send grab/claim commands to the group (cctip_bot reads these)
    for cmd in ["/grab", "/claim"]:
        try:
            await client.send_message(chat, cmd)
            log(f"  📤 Sent '{cmd}' to group")
            await safe_delay(1, 2)
        except Exception as e:
            log(f"  ⚠️  {cmd} failed: {e}")

    # 4. Notify yourself
    msg_text = getattr(message, "message", "") or ""
    await notify_self(
        client,
        f"🪙 Grabbed!\n"
        f"Group: {chat_title}\n"
        f"Type: {giveaway_type}\n"
        f"Button clicked: {'Yes' if clicked else 'No'}\n"
        f"Message: {msg_text[:200]}\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    log("🔔 Notification sent to Saved Messages")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    log("🚀 @cctip_bot Grabber starting …")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        log("❌ Not logged in — run: python do_login.py --request")
        return

    me = await client.get_me()
    log(f"✅ Logged in as: {me.first_name} (@{me.username})")

    # ── Step 1: Try to join seed groups (best-effort, many may not exist) ──
    log("📋 Checking seed @cctip_bot groups …")
    for g in SEED_GROUPS:
        try:
            entity = await client.get_entity(g)
            await join_group(client, entity)
            await safe_delay(1, 2)
        except Exception:
            pass  # Group doesn't exist or private — skip silently

    # ── Step 2: Scan existing groups for @cctip_bot presence ──────────────
    cctip_groups = await scan_my_groups(client)
    log(f"📊 Found {len(cctip_groups)} group(s) with @cctip_bot active")

    # ── Step 3: Event handler — only fire on messages FROM @cctip_bot ──────
    @client.on(events.NewMessage())
    async def handler(event):
        msg = event.message
        text = msg.message or ""

        # Skip our own outgoing messages
        if event.out:
            return

        # Only care about messages from @cctip_bot / @Cwallet_com_Bot
        try:
            sender = await event.get_sender()
        except Exception:
            return

        if sender is None:
            return

        sender_username = (getattr(sender, "username", "") or "").lower()
        if sender_username not in CCTIP_USERNAMES:
            return

        # Only act if this looks like a giveaway announcement
        match = GIVEAWAY_PATTERN.search(text)
        if not match:
            return

        giveaway_type = match.group(0)

        try:
            chat = await event.get_chat()
        except Exception:
            return

        await grab_giveaway(client, chat, msg, giveaway_type)

    log(f"👂 Watching for @cctip_bot giveaways in ALL your groups … (running 24/7)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
