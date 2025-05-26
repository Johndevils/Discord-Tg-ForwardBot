import os
import discord
import requests

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

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
    if message.author == client.user:
        return

    if message.channel.id == DISCORD_CHANNEL_ID:
        author = message.author.name
        text = message.content or ""
        caption = f"<b>{author}</b>:\n{text}" if text else f"<b>{author}</b>"

        if message.attachments:
            for i, attachment in enumerate(message.attachments):
                if attachment.content_type and attachment.content_type.startswith('image'):
                    img_bytes = await attachment.read()
                    cap = caption if i == 0 else ""
                    resp = send_photo_to_telegram(img_bytes, cap)
                    if resp.status_code != 200:
                        print("Failed to send photo to Telegram:", resp.text)
                else:
                    if i == 0 and text:
                        resp = send_text_to_telegram(caption + "\n" + attachment.url)
                        if resp.status_code != 200:
                            print("Failed to send message to Telegram:", resp.text)
                    else:
                        resp = send_text_to_telegram(attachment.url)
        else:
            if text:
                resp = send_text_to_telegram(caption)
                if resp.status_code != 200:
                    print("Failed to send message to Telegram:", resp.text)

client.run(DISCORD_TOKEN)
