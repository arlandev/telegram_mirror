from telethon import TelegramClient, events
from telethon.tl.types import User, Message, MessageService
from telethon.tl.types.messages import ChannelMessages
from langdetect import detect
from deep_translator import GoogleTranslator
import textwrap
import os
import requests
import json
import random
import aiohttp
import nextcord
from dotenv import load_dotenv

load_dotenv()

url_chat = os.environ.get("WEBHOOK")

appid = os.environ.get("APPID")
apihash = os.environ.get("APIHASH")
apiname = os.environ.get("APINAME")
dlloc = os.environ.get("DLLOC")
input_channels_entities = os.environ.get("INPUT_CHANNELS")
blacklist = os.environ.get("BLACKLIST")
translate = bool(os.environ.get("TRANSLATE"))

if blacklist == 'True':
    blacklist = True

if input_channels_entities is not None:
    input_channels_entities = list(map(int, input_channels_entities.split(',')))

async def imgur(mediafile):
    url = "https://api.imgur.com/3/upload"

    payload = {
        'album': 'ALBUMID',
        'type': 'file',
        'disable_audio': '0'
    }

    files = [
        ('video', open(mediafile, 'rb'))
    ]

    headers = {
        'Authorization': str(random.randint(1, 10000000000))
    }

    response = requests.post(url, headers=headers, data=payload, files=files)
    return json.loads(response.text)

def start():
    client = TelegramClient(apiname, appid, apihash)
    client.start()
    print('Started')
    print(f'Input channels: {input_channels_entities}')
    print(f'Blacklist: {blacklist}')

    @client.on(events.NewMessage(chats=input_channels_entities, blacklist_chats=blacklist))
    async def handler(event):
        if isinstance(event.chat, User):
                return  # to ignore messages from bots or users

        msg = event.message.message
        thread_id = 0
        msg_obj = event.message
        if msg_obj.reply_to and msg_obj.reply_to.forum_topic:
            thread_id = msg_obj.reply_to.reply_to_top_id
        else: 
            try:
                thread_id = msg_obj.reply_to.forum_topic.id
            except Exception as threadError:
                print("Error obtaining thread ID")
        print(f"Thread ID: {thread_id}")

        if translate:
            try:
                if msg != '' and detect(textwrap.wrap(msg, 2000)[0]) != 'en':
                    msg += '\n\n' + 'Translated:\n\n' + GoogleTranslator(source='auto', target='en').translate(msg)
            except:
                pass

        if event.message.sender.username is not None:
            username = event.message.sender.username + ' in ' + event.chat.title
        else:
            username = event.chat.title

        if event.message.reply_to_msg_id:
            
            # If the message is a reply, fetch the original message
            original_message = await client.get_messages(event.chat, ids=event.message.reply_to_msg_id)
            print(original_message)
            if isinstance(event.message, MessageService):
                thread_id = event.message.id
                print(f"obtained thread id: {thread_id}")
            else:
                pass
            
            
            if original_message.sender.username:
                original_username = original_message.sender.username
            else:
                original_username = original_message.chat.title

            # Mirror the original message and the reply
            original_text = original_message.text
            if event.message.reply_to is None or original_text == "" or original_text == "None":
                await send_to_webhook(message_to_send, username, event.chat.id, thread_id)
            else:
                reply_text = event.message.message
                
                # Handle images in the reply or original message
                if event.message.media:
                    # If the reply contains media, download and send it
                    path = await event.message.download_media(dlloc)
                    await pic(path, reply_text, username, event.chat.id, thread_id)
                    os.remove(path)

                if original_message.media:
                    # If the original message contains media, download and send it
                    path = await original_message.download_media(dlloc)
                    await pic(path, original_text, original_username, event.chat.id, thread_id)
                    os.remove(path)

                # Send the reply text to the webhook
                message_to_send = f"Original Message from {original_username}: \n{original_text}\n\nReply from {username}: \n{reply_text}"
                await send_to_webhook(message_to_send, username, event.chat.id, thread_id)
        else:
            if event.message.media is not None and event.message.file:
                dur = event.message.file.duration
                if dur is None:
                    dur = 1

                if dur > 60 or event.message.file.size > 209715201:
                    print('Media too long or too big!')
                    msg += f"\n\nLink to Video: https://t.me/c/{event.chat.id}/{event.message.id}"
                    await send_to_webhook(msg, username, event.chat.id, thread_id)
                    return
                else:
                    path = await event.message.download_media(dlloc)
                    if event.message.file.size > 8388608:
                        await picimgur(path, msg, username, event.chat.id, thread_id)
                    else:
                        await pic(path, msg, username, event.chat.id, thread_id)
                    os.remove(path)
            else:
                await send_to_webhook(msg, username, event.chat.id, thread_id)
    client.run_until_disconnected()

async def picimgur(filem, message, username, channel_id, thread_id):
    channel_id = str(channel_id)
    thread_id = str(thread_id)
    async with aiohttp.ClientSession() as session:
        try:
            print('Sending w media Imgur')

            webhook = nextcord.Webhook.from_url(url_chat, session=session)
            
            message = f"{message} \n\n\n@everyone"

            try:
                image = await imgur(filem)
                image = image['data']['link']
                image2 = await imgur(filem)
                image2 = image2['data']['link']
                print(f'Imgur: {image}')
                await webhook.send(content=image, username=username)
            except Exception as ee:
                print(f'Error {ee.args}')
            

            for line in textwrap.wrap(message, 2000, replace_whitespace=False):
                await webhook.send(content=line, username=username)
            
        except Exception as e:
            print(f'Error {e.args}')

async def pic(filem, message, username, channel_id, thread_id):
    channel_id = str(channel_id)
    thread_id = str(thread_id)
    async with aiohttp.ClientSession() as session:
        try:
            print('Sending w media')
            print(f"Channel ID: {channel_id}")
            print(f"Thread ID: {thread_id}")
            
            webhook = nextcord.Webhook.from_url(url_chat, session=session)

            message = f"{message} \n\n\n@everyone"
            webhook = nextcord.Webhook.from_url(url_chat, session=session)

            try:
                f = nextcord.File(filem)
                f2 = nextcord.File(filem)
                await webhook.send(file=f, username=username)
            except:
                print('Uploading to imgur')
                try:
                    image = await imgur(filem)
                    image = image['data']['link']
                    image2 = await imgur(filem)
                    image2 = image2['data']['link']
                    print(f'Imgur: {image}')
                    await webhook.send(content=image, username=username)
                except Exception as ee:
                    print(f'Error {ee.args}')
            for line in textwrap.wrap(message, 2000, replace_whitespace=False):
                await webhook.send(content=line, username=username)
                
        except Exception as e:
            print(f'Error {e.args}')

async def send_to_webhook(message, username, channel_id, thread_id):
    channel_id = str(channel_id)
    thread_id = str(thread_id)
    async with aiohttp.ClientSession() as session:
        print(f"Channel ID: {channel_id}")
        print(f"Thread ID: {thread_id}")
        print('Sending w/o media')
        
        message = f"{message} \n\n\n@everyone"
        webhook = nextcord.Webhook.from_url(url_chat, session=session)
        for line in textwrap.wrap(message, 2000, replace_whitespace=False):
            await webhook.send(content=line, username=username)


if __name__ == "__main__":
    start()