import os
import threading
import asyncio
from flask import Flask, jsonify
import discord
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')  # like -1001234567890
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PORT = int(os.getenv('PORT', 10000))

app = Flask(__name__)

# In-memory store for new messages to forward
pending_messages = []

@app.route('/')
def home():
    return '✅ Discord to Telegram bot is running!'

@app.route('/scrap')
def scrap():
    # Forward all collected messages to Telegram, then clear the list
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
        pending_messages = []  # Clear after sending
        return jsonify({"status": "success", "message": f"Forwarded {count} messages."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def send_photo_to_telegram(photo_bytes, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('image.jpg', photo_bytes)}
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    return requests.post(url, files=files, data=data)

def send_text_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'text': text,
        'parse_mode': 'HTML'
    }
    return requests.post(url, data=data)

@client.event
async def on_ready():
    print(f'✅ Bot is online as {client.user}')
    print(f'Listening on Discord Channel ID: {DISCORD_CHANNEL_ID}')
    print(f'Forwarding to Telegram Channel ID: {TELEGRAM_CHANNEL}')
    try:
        send_text_to_telegram(
            "<b>✅ Bot Started Successfully!</b>\n"
            "🔄 <i>Now forwarding messages from Discord to Telegram every 5 minutes.</i>\n"
            f"🎯 <b>Listening on:</b> <code>{DISCORD_CHANNEL_ID}</code>\n"
            f"📢 <b>Target Channel:</b> <code>{TELEGRAM_CHANNEL}</code>"
        )
    except Exception as e:
        print(f"❌ Failed to send Telegram startup message: {e}")

@client.event
async def on_message(message):
    global pending_messages

    if message.author == client.user:
        return

    if message.channel.id == DISCORD_CHANNEL_ID:
        author = message.author.name
        text = message.content or ""
        caption = f"<b>{author}</b>:\n{text}" if text else f"<b>{author}</b>"

        if message.attachments:
            for i, attachment in enumerate(message.attachments):
                try:
                    if attachment.content_type and attachment.content_type.startswith('image'):
                        img_bytes = await attachment.read()
                        cap = caption if i == 0 else ""
                        pending_messages.append({
                            'type': 'photo',
                            'photo_bytes': img_bytes,
                            'caption': cap
                        })
                    else:
                        link_text = f"{caption}\n{attachment.url}" if i == 0 and text else attachment.url
                        pending_messages.append({
                            'type': 'text',
                            'content': link_text
                        })
                except Exception as e:
                    print(f"❌ Error processing attachment: {e}")
        elif text:
            pending_messages.append({
                'type': 'text',
                'content': caption
            })

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
