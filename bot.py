import os
import discord
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# Enable message content intent
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
    response = requests.post(url, files=files, data=data)
    return response

def send_text_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHANNEL,
        'text': text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data)
    return response

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Only process messages from the specified channel
    if message.channel.id == DISCORD_CHANNEL_ID:
        author = message.author.name
        text = message.content or ""
        caption = f"<b>{author}</b>:\n{text}" if text else f"<b>{author}</b>"

        # If message has attachments (like images)
        if message.attachments:
            for i, attachment in enumerate(message.attachments):
                if attachment.content_type and attachment.content_type.startswith('image'):
                    try:
                        img_bytes = await attachment.read()
                        cap = caption if i == 0 else ""
                        resp = send_photo_to_telegram(img_bytes, cap)
                        if resp.status_code != 200:
                            print("Failed to send photo:", resp.text)
                    except Exception as e:
                        print("Error sending image:", e)
                else:
                    try:
                        if i == 0 and text:
                            full_text = caption + "\n" + attachment.url
                        else:
                            full_text = attachment.url
                        resp = send_text_to_telegram(full_text)
                        if resp.status_code != 200:
                            print("Failed to send attachment URL:", resp.text)
                    except Exception as e:
                        print("Error sending attachment:", e)
        else:
            if text:
                resp = send_text_to_telegram(caption)
                if resp.status_code != 200:
                    print("Failed to send text message:", resp.text)

# Run the bot
client.run(DISCORD_TOKEN)
