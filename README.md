# Telegram Crypto Giveaway Userbot

Monitors Telegram groups for crypto airdrops and giveaways, auto-participates, and notifies you instantly.

## Setup

### 1. Get Telegram API credentials
1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click **API Development Tools**
4. Create an app — copy your **API ID** and **API Hash**

### 2. Configure environment
```bash
cp .env.template .env
```
Open `.env` and fill in:
```
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
PHONE_NUMBER=+12025551234
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run
```bash
python main.py
```
On **first run** it will ask for your phone number and a verification code Telegram sends you. After that, the session is saved and it never asks again.

## What it does

| Feature | Details |
|---|---|
| **Monitor** | Watches 25+ groups for keywords: airdrop, giveaway, rain, grab, claim, etc. |
| **Auto-join** | Joins any group where a giveaway is detected if not already a member |
| **Auto-grab** | Clicks inline buttons (Grab/Claim/Join), replies "grab", sends `/grab` and `/claim` to @cctip_bot |
| **Notify** | Sends a message to your Saved Messages + prints to console |
| **Safe delays** | Random 2–5 second pauses between actions to avoid flood bans |
| **Keep-alive** | Flask server on port 8080 so Replit doesn't sleep |

## Files

```
telegram-userbot/
├── main.py           ← Entry point (userbot logic)
├── keep_alive.py     ← Flask ping server (keeps Replit awake)
├── requirements.txt  ← Python dependencies
├── .env.template     ← Copy to .env and fill in your credentials
└── README.md
```

## Adding more groups

Edit the `MONITORED_GROUPS` list in `main.py` — add any username or invite link.

## ⚠️ Important notes
- This is a **userbot** (runs on your personal account), not a BotFather bot.
- Use responsibly — excessive auto-participation can get accounts restricted.
- Keep your `.env` file private — never commit it to GitHub.
