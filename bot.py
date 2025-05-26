import os
import threading
from flask import Flask
import discord
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PORT = int(os.getenv('PORT', 10000))

# Flask server to keep container alive
app = Flask(__name__)

@app.route('/')
def home():
    return 'Discord to Telegram bot is running!'

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Telegram forward functions
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
    print(f'Forwarding messages from Discord Channel ID: {DISCORD_CHANNEL_ID} to Telegram Channel: {TELEGRAM_CHANNEL}')

@client.event
async def on_message(message):
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
                        resp = send_photo_to_telegram(img_bytes, cap)
                        if resp.status_code != 200:
                            print(f"❌ Failed to send image: {resp.text}")
                    else:
                        link_text = f"{caption}\n{attachment.url}" if i == 0 and text else attachment.url
                        resp = send_text_to_telegram(link_text)
                        if resp.status_code != 200:
                            print(f"❌ Failed to send file/link: {resp.text}")
                except Exception as e:
                    print(f"❌ Error processing attachment: {e}")
        elif text:
            try:
                resp = send_text_to_telegram(caption)
                if resp.status_code != 200:
                    print(f"❌ Failed to send text message: {resp.text}")
            except Exception as e:
                print(f"❌ Error sending text message: {e}")

# Start Flask in a thread and then start the bot
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
