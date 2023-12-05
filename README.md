# Telegram-To-Discord
Reflects specified Telegram Channel messages into a Discord Webhook link, including media files attached to the message. If messages are non-english, they are translated into english.

# Requirements

- python 3.11 or later
- python pip -> requirements.txt
- discord bot token https://discord.com/developers/
- telegram API tokens https://core.telegram.org/bots/api

# How to run
```py
#download the repo and extract to an empty folder
#open a CLI ex. CMD,PS,GitBash in the directory
pip3 install -r requirements.txt
#rename sample.env to .env
#edit info in .env
#obtain your APPID and HASH here https://core.telegram.org/api/obtaining_api_id
python3 main.py
#OR
py main.py
```
