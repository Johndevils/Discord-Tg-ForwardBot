import os
import threading
from flask import Flask, jsonify
import discord
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')  # e.g., -1001234567890
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PORT = int(os.getenv('PORT', 10000))

# Flask server setup
app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Discord to Telegram bot is running!'

# Pending messages for 5-min cron job
pending_messages = []

@app.route('/scrap', methods=['GET'])
def scrap():
    global pending_messages
    if not pending_messages:
        return jsonify({"status": "success", "message": "No new messages to forward."})

    try:
        for msg in pending_messages:
            if msg['type'] == 'text':
                send_text_to_telegram(msg['content'])
            elif msg['type'] == 'photo':
                send_photo_to_telegram(msg['photo_bytes'], msg['caption'])
        count = len(pending_messages)
        pending_messages = []
        return jsonify({"status": "success", "message": f"Forwarded {count} messages."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Start Flask in thread
def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# Setup Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Telegram functions
def send_text_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'text': text,
        'parse_mode': 'HTML'
    }
    return requests.post(url, data=data)

def send_photo_to_telegram(photo_bytes, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('image.jpg', photo_bytes)}
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    return requests.post(url, files=files, data=data)

# Discord events
@client.event
async def on_ready():
    print(f'✅ Bot is online as {client.user}')
    print(f'Listening on Discord Channel ID: {DISCORD_CHANNEL_ID}')
    print(f'Forwarding to Telegram Channel ID: {TELEGRAM_CHANNEL}')

    try:
        send_text_to_telegram(
            "<b>✅ Bot Started Successfully!</b>\n"
            "🔄 Forwarding Discord messages to Telegram every 5 minutes.\n"
            f"🎯 Discord Channel: <code>{DISCORD_CHANNEL_ID}</code>\n"
            f"📢 Telegram Channel: <code>{TELEGRAM_CHANNEL}</code>"
        )
    except Exception as e:
        print(f"❌ Telegram start message error: {e}")

    try:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("✅ Bot is live and collecting messages for forwarding!")
    except Exception as e:
        print(f"❌ Discord start message error: {e}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id != DISCORD_CHANNEL_ID:
        return

    author = message.author.name
    text = message.content or ""
    caption = f"<b>{author}</b>:\n{text}" if text else f"<b>{author}</b>"

    if message.attachments:
        for i, attachment in enumerate(message.attachments):
            try:
                if attachment.content_type and attachment.content_type.startswith('image'):
                    img_bytes = await attachment.read()
                    pending_messages.append({
                        "type": "photo",
                        "photo_bytes": img_bytes,
                        "caption": caption if i == 0 else ""
                    })
                else:
                    link_text = f"{caption}\n{attachment.url}" if i == 0 else attachment.url
                    pending_messages.append({
                        "type": "text",
                        "content": link_text
                    })
            except Exception as e:
                print(f"❌ Error reading attachment: {e}")
    elif text:
        pending_messages.append({
            "type": "text",
            "content": caption
        })

# Start Flask and Discord bot
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
