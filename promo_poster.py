"""
promo_poster.py
────────────────
Runs alongside main.py — posts a promotional Stake.com affiliate message
to your channel every N hours, keeping the channel active and driving
affiliate signups.

Run: python promo_poster.py   (runs forever)
"""

import asyncio
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()
API_ID   = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]

AFFILIATE_LINK  = "https://stake.com/?c=Natal"
SITE_LINK       = "https://stakecruncher.com"
CHANNEL_ID_FILE = "channel_id.txt"

# Post every 4 hours
POST_INTERVAL_HOURS = 4

# Rotating promo messages — keeps it fresh so it doesn't look spammy
PROMO_MESSAGES = [
    f"""🌧️ Did you catch today's rain?

Stake.com Telegram groups drop free crypto every day — tips, rain, airdrops.
We track them all and post live alerts right here.

🔔 Turn on notifications!
📊 Stake tools: {SITE_LINK}
🎁 New to Stake? Sign up free: {AFFILIATE_LINK}""",

    f"""💰 Free Stake.com balance — no deposit needed

Rain events happen daily in Stake's Telegram groups. Our bot grabs them automatically and posts every alert here.

📊 Calculate your RTP, track bets, verify fairness:
👉 {SITE_LINK}

🎰 Play on Stake (use code for bonus):
👉 {AFFILIATE_LINK}""",

    f"""🚨 RAIN ALERT CHANNEL

This channel posts every free crypto giveaway happening in Stake.com Telegram communities — in real time.

Tools to maximize your Stake experience:
📈 Profit/loss calculator
🎰 RTP analyzer
✅ Provably fair verifier

👉 {SITE_LINK}

Sign up on Stake: {AFFILIATE_LINK}""",

    f"""📊 Stake Cruncher — Free Tools for Stake Players

✅ Profit & loss tracker
✅ VIP level calculator
✅ Bonus value calculator
✅ Provably fair verifier
✅ Live bet feed

All free, no sign-up:
👉 {SITE_LINK}

Play on Stake: {AFFILIATE_LINK}""",

    f"""🎁 How to get free crypto on Stake.com:

1️⃣ Join Stake.com Telegram groups
2️⃣ Watch for /rain and /airdrop commands from @cctip_bot
3️⃣ Be first to type "grab"

OR just follow this channel — we post every alert automatically! 🔔

Sign up on Stake: {AFFILIATE_LINK}
Tools: {SITE_LINK}""",
]


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


async def main():
    if not os.path.exists(CHANNEL_ID_FILE):
        print(f"❌ {CHANNEL_ID_FILE} not found. Run setup_channel.py first.")
        return

    channel_id = int(open(CHANNEL_ID_FILE).read().strip())

    client = TelegramClient("userbot_session", API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Not logged in.")
        return

    me = await client.get_me()
    log(f"✅ Promo poster running as {me.first_name} | posting every {POST_INTERVAL_HOURS}h")
    log(f"   Channel ID: {channel_id}")

    msg_index = 0
    while True:
        try:
            msg = PROMO_MESSAGES[msg_index % len(PROMO_MESSAGES)]
            await client.send_message(channel_id, msg, link_preview=False)
            log(f"📤 Promo #{msg_index + 1} posted to channel")
            msg_index += 1
        except Exception as e:
            log(f"⚠️  Failed to post promo: {e}")

        # Wait N hours before next post
        await asyncio.sleep(POST_INTERVAL_HOURS * 3600)


if __name__ == "__main__":
    asyncio.run(main())
