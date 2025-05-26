import os
import threading
import asyncio
from flask import Flask
import discord
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')  # e.g., -1001234567890
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
PORT = int(os.getenv('PORT', 10000))

# Flask app to keep the bot alive on Render.com
app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Discord to Telegram bot is running!'

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# Setup Discord client with intents to read messages
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Telegram helpers
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
    
    # Send startup message to Telegram
    try:
        send_text_to_telegram(
            "<b>✅ Bot Started Successfully!</b>\n"
            "🔄 <i>Now forwarding messages from Discord to Telegram.</i>\n"
            f"🎯 <b>Listening on:</b> <code>{DISCORD_CHANNEL_ID}</code>\n"
            f"📢 <b>Target Channel:</b> <code>{TELEGRAM_CHANNEL}</code>"
        )
    except Exception as e:
        print(f"❌ Failed to send Telegram startup message: {e}")
    
    # Send startup message to Discord channel
    try:
        channel = client.get_channel(DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("✅ Bot is online and forwarding messages to Telegram!")
        else:
            print("❌ Discord channel not found!")
    except Exception as e:
        print(f"❌ Failed to send Discord startup message: {e}")

# Track last message ID to avoid duplicates
last_message_id = None

async def cronjob_forwarder():
    global last_message_id
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            channel = client.get_channel(DISCORD_CHANNEL_ID)
            if not channel:
                print("❌ Discord channel not found during cronjob.")
                await asyncio.sleep(300)
                continue

            # Fetch messages after last processed message ID
            if last_message_id:
                messages = await channel.history(limit=10, after=discord.Object(id=last_message_id)).flatten()
            else:
                messages = await channel.history(limit=10).flatten()

            messages = sorted(messages, key=lambda m: m.id)  # oldest first

            for message in messages:
                if message.author == client.user:
                    continue  # skip bot's own messages

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

                last_message_id = message.id

        except Exception as e:
            print(f"❌ Error in cronjob loop: {e}")

        await asyncio.sleep(300)  # Poll every 5 minutes

# Start Flask + Discord bot + cronjob
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    client.loop.create_task(cronjob_forwarder())
    client.run(DISCORD_TOKEN)
