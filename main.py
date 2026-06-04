"""
main.py – Telegram Userbot — @cctip_bot Grabber + Channel Promo Poster
───────────────────────────────────────────────────────────────────────
1. Scans your groups for @cctip_bot
2. Auto-grabs every rain / airdrop / draw / giveaway
3. Posts every grab to your promo channel with affiliate link
4. Posts periodic promos to channel every 4 hours
5. Notifies Saved Messages on every grab
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
)
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest

from keep_alive import keep_alive

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE    = os.environ["TELEGRAM_PHONE"]

SESSION_NAME    = "userbot_session"
CHANNEL_ID_FILE = "channel_id.txt"
AFFILIATE_LINK  = "https://stake.com/?c=Natal"
SITE_LINK       = "https://stakecruncher.com"

# Post a promo to channel every 4 hours
PROMO_INTERVAL_HOURS = 4

# ─── @cctip_bot usernames ─────────────────────────────────────────────────────
CCTIP_USERNAMES = {"cctip_bot", "cwallet_com_bot", "cctipcoin_bot"}

# ─── Giveaway trigger pattern ─────────────────────────────────────────────────
GIVEAWAY_PATTERN = re.compile(
    r"/airdrop|/rain|/draw|/giveaway|/lucky|/tip\b|grab a share|airdrop started|rain started|giveaway started",
    re.IGNORECASE,
)

# ─── Buttons to click ────────────────────────────────────────────────────────
GRAB_BUTTON_LABELS = {
    "grab", "grab a share", "claim", "join", "participate",
    "get", "claim reward", "take", "join airdrop",
}

GRAB_KEYWORD = "grab"

# ─── Seed groups to try joining ───────────────────────────────────────────────
SEED_GROUPS = [
    "Cwallet_official", "cctip_official", "cwallet_announcements",
    "CwalletGlobal", "CCTipCommunity", "cctip_rain", "cwallet_rain",
    "CryptoRainOfficial", "RainCrypto", "CCTipAirdrop",
    "CwalletAirdrop", "TipBotCrypto", "CryptoTipRain",
]

# ─── Rotating promo messages ──────────────────────────────────────────────────
PROMO_MESSAGES = [
    f"🌧️ Free crypto rain alerts — live from Stake.com Telegram groups!\n\n📊 Stake tools: {SITE_LINK}\n🎁 Sign up on Stake: {AFFILIATE_LINK}",
    f"💰 Get free Stake.com balance — we track every rain, tip & airdrop in real time.\n\n👉 {SITE_LINK}\n🎰 Play on Stake: {AFFILIATE_LINK}",
    f"📊 Free Stake tools: profit tracker · RTP calculator · provably fair verifier\n\n👉 {SITE_LINK}\n\nNew to Stake? {AFFILIATE_LINK}",
    f"🚨 LIVE ALERT CHANNEL — every @cctip_bot giveaway posted here instantly.\n\n📈 {SITE_LINK}\n🎁 {AFFILIATE_LINK}",
    f"🎰 How to get free crypto on Stake.com:\n1️⃣ Join Stake Telegram groups\n2️⃣ Watch for /rain and /airdrop\n3️⃣ Type 'grab' first!\n\nOR follow this channel 🔔\n\n{AFFILIATE_LINK}",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def load_channel_id():
    if os.path.exists(CHANNEL_ID_FILE):
        try:
            return int(open(CHANNEL_ID_FILE).read().strip())
        except Exception:
            pass
    return None


async def safe_delay(a=2.0, b=5.0):
    await asyncio.sleep(random.uniform(a, b))


async def post_to_channel(client, channel_id, text):
    """Post a message to the promo channel."""
    if not channel_id:
        return
    try:
        await client.send_message(channel_id, text, link_preview=False)
        log("📢 Posted to promo channel")
    except Exception as e:
        log(f"  ⚠️  Channel post failed: {e}")


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
        await asyncio.sleep(e.seconds)
    except Exception:
        pass


async def cctip_bot_in_group(client, group):
    for uname in CCTIP_USERNAMES:
        try:
            await client(GetParticipantRequest(group, uname))
            return True
        except Exception:
            continue
    return False


async def scan_my_groups(client):
    found = []
    log("🔍 Scanning your groups for @cctip_bot …")
    async for dialog in client.iter_dialogs():
        if not dialog.is_group and not dialog.is_channel:
            continue
        try:
            if await cctip_bot_in_group(client, dialog.entity):
                found.append(dialog.entity)
                log(f"  ✅ @cctip_bot in: {dialog.title}")
                await asyncio.sleep(0.5)
        except Exception:
            continue
    return found


async def try_click_buttons(message):
    if not message.reply_markup:
        return False
    clicked = False
    for row in getattr(message.reply_markup, "rows", []):
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


async def grab_giveaway(client, chat, message, giveaway_type, channel_id):
    chat_title = getattr(chat, "title", None) or str(chat.id)
    msg_text   = getattr(message, "message", "") or ""
    log(f"🎯 GRAB triggered in [{chat_title}] — {giveaway_type}")

    await safe_delay(1, 3)

    # 1. Click inline button
    clicked = await try_click_buttons(message)
    await safe_delay(1, 2)

    # 2. Reply "grab"
    try:
        await message.reply(GRAB_KEYWORD)
        log(f"  📩 Replied '{GRAB_KEYWORD}'")
    except ChatWriteForbiddenError:
        log("  ⚠️  Write forbidden")
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception as e:
        log(f"  ⚠️  Reply failed: {e}")

    await safe_delay(1, 2)

    # 3. Send /grab /claim commands
    for cmd in ["/grab", "/claim"]:
        try:
            await client.send_message(chat, cmd)
            log(f"  📤 Sent '{cmd}'")
            await safe_delay(1, 2)
        except Exception as e:
            log(f"  ⚠️  {cmd} failed: {e}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 4. Post to promo channel
    channel_post = (
        f"🪙 FREE CRYPTO GRABBED!\n\n"
        f"Type: {giveaway_type}\n"
        f"Group: {chat_title}\n"
        f"Time: {now}\n\n"
        f"🎰 Want free Stake balance?\n"
        f"👉 {AFFILIATE_LINK}\n\n"
        f"📊 Stake tools: {SITE_LINK}"
    )
    await post_to_channel(client, channel_id, channel_post)

    # 5. Notify Saved Messages
    await notify_self(client,
        f"🪙 Grabbed!\nGroup: {chat_title}\nType: {giveaway_type}\n"
        f"Button: {'Yes' if clicked else 'No'}\nMsg: {msg_text[:150]}\nTime: {now}"
    )
    log("🔔 Notified Saved Messages")


async def promo_loop(client, channel_id):
    """Post rotating affiliate promos to the channel every 4 hours."""
    if not channel_id:
        log("⚠️  No channel ID found — promo loop skipped. Run setup_channel.py first.")
        return
    idx = 0
    while True:
        await asyncio.sleep(PROMO_INTERVAL_HOURS * 3600)
        try:
            await client.send_message(channel_id, PROMO_MESSAGES[idx % len(PROMO_MESSAGES)], link_preview=False)
            log(f"📢 Promo #{idx+1} posted to channel")
            idx += 1
        except Exception as e:
            log(f"⚠️  Promo post failed: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    log("🚀 Stake Cruncher Userbot starting …")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        log("❌ Not logged in — run: python do_login.py --request")
        return

    me = await client.get_me()
    log(f"✅ Logged in as: {me.first_name} (@{me.username})")

    # Load promo channel ID (created by setup_channel.py)
    channel_id = load_channel_id()
    if channel_id:
        log(f"📢 Promo channel loaded: ID={channel_id}")
    else:
        log("⚠️  No promo channel yet — run setup_channel.py to create one")

    # Join seed groups
    log("📋 Checking seed @cctip_bot groups …")
    for g in SEED_GROUPS:
        try:
            entity = await client.get_entity(g)
            await join_group(client, entity)
            await safe_delay(1, 2)
        except Exception:
            pass

    # Scan existing groups for @cctip_bot
    cctip_groups = await scan_my_groups(client)
    log(f"📊 Found {len(cctip_groups)} group(s) with @cctip_bot")

    # Start promo loop in background
    asyncio.create_task(promo_loop(client, channel_id))

    # Event handler — only fires on @cctip_bot messages
    @client.on(events.NewMessage())
    async def handler(event):
        if event.out:
            return
        try:
            sender = await event.get_sender()
        except Exception:
            return
        if sender is None:
            return
        if (getattr(sender, "username", "") or "").lower() not in CCTIP_USERNAMES:
            return
        text = event.message.message or ""
        match = GIVEAWAY_PATTERN.search(text)
        if not match:
            return
        try:
            chat = await event.get_chat()
        except Exception:
            return
        await grab_giveaway(client, chat, event.message, match.group(0), channel_id)

    log("👂 Watching for @cctip_bot giveaways 24/7 …")
    await client.run_until_disconnected()


if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
