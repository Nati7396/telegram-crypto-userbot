"""
main.py – Telegram Userbot (Telethon)
──────────────────────────────────────
Monitors a list of Telegram groups/channels for crypto giveaways & airdrops,
auto-participates, and notifies you (Saved Messages) + the console.

Requirements: telethon, flask, python-dotenv
Run:          python main.py
"""

import asyncio
import os
import random
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import (
    ChatWriteForbiddenError,
    FloodWaitError,
    UserAlreadyParticipantError,
)
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import KeyboardButtonCallback

from keep_alive import keep_alive

# ─── Load environment variables from .env ────────────────────────────────────
load_dotenv()

API_ID      = int(os.environ["API_ID"])
API_HASH    = os.environ["API_HASH"]
PHONE       = os.environ["PHONE_NUMBER"]

# ─── Telethon session (saved to disk so login is only needed once) ────────────
SESSION_NAME = "userbot_session"

# ─── Keywords that signal a giveaway / airdrop is happening ──────────────────
GIVEAWAY_KEYWORDS = [
    "airdrop",
    "giveaway",
    r"/rain",
    r"/airdrop",
    r"/tip",
    "grab",
    r"/grab",
    "claim",
    r"/claim",
    "free",
    "@cctip_bot",
    "rain",
    "/giveaway",
    "/draw",
    "/lucky",
    "luckybox",
    "token drop",
    "crypto drop",
    "participate",
    "join to win",
    "free tokens",
    "free coins",
]

# Compile into one fast regex (case-insensitive)
KEYWORD_PATTERN = re.compile(
    "|".join(re.escape(k) for k in GIVEAWAY_KEYWORDS),
    re.IGNORECASE,
)

# ─── Buttons we try to click when they appear ────────────────────────────────
GRAB_BUTTON_LABELS = {
    "grab", "claim", "join", "participate", "get", "grab a share",
    "join airdrop", "claim reward", "take", "get tokens",
}

# ─── Commands sent to @cctip_bot after detecting a giveaway ──────────────────
CCTIP_COMMANDS = ["/grab", "/claim"]

# ─── 20+ popular @cctip_bot Telegram groups to monitor from the start ────────
MONITORED_GROUPS = [
    # Username-based (public groups/channels)
    "cctip_announcements",
    "CryptoComOfficial",
    "BinanceEnglish",
    "CoinMarketCapGlobal",
    "KuCoinGlobalCommunity",
    "AirdropAlertCom",
    "AirdropBob",
    "AirdropHunter",
    "CryptoAirdropIntel",
    "FreeAirdropNews",
    "AirdropDetective",
    "CoinHuntWorld",
    "CryptoGiveawayHub",
    "TronAirdrops",
    "BSCAirdrops",
    "SolanaAirdrops",
    "PolygonAirdropHub",
    "EthereumAirdrops",
    "CryptoRainGroup",
    "CryptoTipBot",
    "AirdropKingdom",
    "CryptoFreebies",
    "AirdropHuntersClub",
    "GrabCryptoNow",
    "CCTipCommunity",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def log(msg: str):
    """Print a timestamped message to the console."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


async def safe_delay(min_s: float = 2.0, max_s: float = 5.0):
    """Random delay to avoid Telegram flood bans."""
    delay = random.uniform(min_s, max_s)
    log(f"  ⏱  Waiting {delay:.1f}s before next action …")
    await asyncio.sleep(delay)


async def notify_self(client: TelegramClient, text: str):
    """Send a notification to your own Saved Messages."""
    try:
        await client.send_message("me", text)
    except Exception as exc:
        log(f"  [notify_self] Could not send self-message: {exc}")


async def join_group(client: TelegramClient, entity):
    """Try to join a group/channel the account is not yet in."""
    try:
        await client(JoinChannelRequest(entity))
        log(f"  ✅ Joined group: {getattr(entity, 'title', entity)}")
    except UserAlreadyParticipantError:
        pass  # Already a member – fine
    except FloodWaitError as e:
        log(f"  ⚠️  Flood wait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as exc:
        log(f"  ❌ Could not join group: {exc}")


async def try_click_buttons(client: TelegramClient, message):
    """Click any inline buttons that match our grab labels."""
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
                    log(f"  🖱️  Clicked button: '{button.text}'")
                    clicked = True
                    await safe_delay()
                except Exception as exc:
                    log(f"  ⚠️  Button click failed: {exc}")
    return clicked


async def try_send_grab_commands(
    client: TelegramClient, chat, message, keyword_found: str
):
    """
    Send /grab or /claim to @cctip_bot (and reply to the giveaway message).
    """
    # 1. Reply to the original giveaway message with "grab"
    try:
        await message.reply("grab")
        log("  📩 Replied 'grab' to giveaway message")
        await safe_delay()
    except ChatWriteForbiddenError:
        log("  ⚠️  Write access forbidden – cannot reply in this chat")
    except FloodWaitError as e:
        log(f"  ⚠️  Flood wait: sleeping {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as exc:
        log(f"  ⚠️  Reply failed: {exc}")

    # 2. Send commands directly to @cctip_bot in the group
    for cmd in CCTIP_COMMANDS:
        try:
            await client.send_message(chat, cmd)
            log(f"  📤 Sent '{cmd}' to the group")
            await safe_delay()
        except Exception as exc:
            log(f"  ⚠️  Could not send '{cmd}': {exc}")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    log("🚀 Telegram Userbot starting …")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    # ── Login (interactive on first run; uses saved session thereafter) ────
    await client.start(phone=PHONE)
    me = await client.get_me()
    log(f"✅ Logged in as: {me.first_name} (@{me.username}) | id={me.id}")

    # ── Join all monitored groups (best-effort; errors are swallowed) ──────
    log("📋 Joining monitored groups …")
    for group in MONITORED_GROUPS:
        try:
            entity = await client.get_entity(group)
            await join_group(client, entity)
            await safe_delay(1.0, 2.5)
        except Exception as exc:
            log(f"  ⚠️  Could not resolve '{group}': {exc}")

    # ─── Event handler: fires on every new message in ANY dialog ──────────
    @client.on(events.NewMessage())
    async def handler(event):
        message = event.message
        text    = message.message or ""

        # Skip empty messages and messages from ourselves
        if not text or event.out:
            return

        # Only react if a giveaway keyword is present
        match = KEYWORD_PATTERN.search(text)
        if not match:
            return

        keyword_found = match.group(0)

        # Resolve the chat entity
        try:
            chat = await event.get_chat()
        except Exception:
            return

        chat_title = getattr(chat, "title", None) or getattr(chat, "username", "Unknown")
        log(f"🎯 Giveaway detected in [{chat_title}] | keyword='{keyword_found}'")
        log(f"   Message: {text[:120].strip()}")

        # If we're not a member, join first
        try:
            await join_group(client, chat)
        except Exception:
            pass

        await safe_delay()

        # 1. Try inline buttons first
        clicked = await try_click_buttons(client, message)

        # 2. Also send grab commands regardless
        await try_send_grab_commands(client, chat, message, keyword_found)

        # 3. Notify yourself
        notification = (
            f"🪙 Giveaway found!\n"
            f"Group: {chat_title}\n"
            f"Keyword: {keyword_found}\n"
            f"Message: {text[:200]}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Button clicked: {'Yes' if clicked else 'No'}"
        )
        await notify_self(client, notification)
        log(f"🔔 Notification sent to Saved Messages")

    log("👂 Listening for giveaways … (press Ctrl+C to stop)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    # Start the keep-alive Flask server in a background thread
    keep_alive()
    # Run the userbot
    asyncio.run(main())
