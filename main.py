import asyncio
import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
import json
from os import environ  # Import PyMuPDF for PDF manipulation

bot_token = environ.get("TOKEN", "") 
api_hash = environ.get("HASH", "") 
api_id = int(environ.get("ID", ""))
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ss = environ.get("STRING", "")
if ss is not None:
    acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    acc.start()
else: 
    acc = None

# Download status
async def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
        
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

# Upload status
async def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)
        
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)

# Progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# Start command
@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(
        message.chat.id, 
        f"__👋 Hi **{message.from_user.mention}**, I am Save Restricted Bot Programmed by Utkarsh, I can send you restricted content by its post link__\n\n"
    )

@bot.on_message(filters.text)
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if "https://t.me/" in message.text and "?start=" in message.text:
        link_parts = message.text.split("?start=")
        bot_username = link_parts[0].split("/")[-1]  # Extract bot username
        start_payload = link_parts[1]  # Extract the start parameter

        if acc is None:
            await bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
            return

        try:
            # Start the bot with the given payload
            start_message = await acc.send_message(bot_username, f"/start {start_payload}")
            await asyncio.sleep(3)  # Wait for initial response

            processed_messages = set()  # Keep track of processed message IDs
            last_msg_time = None

            while True:
                # Fetch the latest messages from the bot using an async generator
                async for msg in acc.get_chat_history(bot_username, limit=50):
                    if msg.id in processed_messages:
                        continue  # Skip already processed messages

                    msg_type = get_message_type(msg)

                    if msg_type in ["video", "photo", "text"]:
                        # Process and download media or text
                        await message.reply_text(f"Processing message ID: {msg.id}")
                        await handle_private(message=message, chatid=bot_username, msgid=msg.id)

                    processed_messages.add(msg.id)  # Mark as processed
                    last_msg_time = msg.date  # Update the time of the last message

                # Check if 1 minute has passed since the last message
                if last_msg_time and (datetime.utcnow() - last_msg_time).total_seconds() > 60:
                    await message.reply_text("No new messages from the bot. Stopping...")
                    break

                # Wait for a short time before checking for new messages
                await asyncio.sleep(5)

        except Exception as e:
            await bot.send_message(message.chat.id, f"**Error**: {e}", reply_to_message_id=message.id)
            

    # Other cases like joining chats or retrieving messages
    elif "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if acc is None:
            await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
            return
        try:
            await acc.join_chat(message.text)
            await bot.send_message(message.chat.id, "**Chat Joined**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "**Chat already Joined**", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "**Invalid Link**", reply_to_message_id=message.id)
        except Exception as e:
            await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

    # Getting message
    elif "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID

        for msgid in range(fromID, toID + 1):
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                if acc is None:
                    await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                    return
                await handle_private(message, chatid, msgid)
            elif "https://t.me/b/" in message.text:
                username = datas[4]
                if acc is None:
                    await bot.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                    return
                try:
                    await handle_private(message, username, msgid)
                except Exception as e:
                    await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)
            else:
                username = datas[3]
                try:
                    msg = await bot.get_messages(username, msgid)
                    await bot.copy_message(message.chat.id, msg.chat.id, msg.id)
                except UsernameNotOccupied:
                    await bot.send_message(message.chat.id, f"**The username is not occupied by anyone**")
                    return
                except Exception as e:
                    await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=None)
            await asyncio.sleep(3)

# Handle private messages
async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    msg = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)

    if "Text" == msg_type:
        await bot.send_message(message.chat.id, msg.text, entities=msg.entities)
        return

    smsg = await bot.send_message(message.chat.id, '__Downloading__')
    dosta = threading.Thread(target=lambda: asyncio.run(downstatus(f'{message.id}downstatus.txt', smsg)), daemon=True)
    dosta.start()
    file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    os.remove(f'{message.id}downstatus.txt')

    upsta = threading.Thread(target=lambda: asyncio.run(upstatus(f'{message.id}upstatus.txt', smsg)), daemon=True)
    upsta.start()

    if "Document" == msg_type:
        try:
            thumb = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            thumb = None
        full_path = file
        filename = "downloads/" + os.path.basename(full_path)
        actual_path = os.path.join(os.path.dirname(full_path), os.path.basename(full_path))
        await bot.send_document(message.chat.id, actual_path, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)
        os.remove(actual_path)
    elif "Video" == msg_type:
        try:
            thumb = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            thumb = None
        await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)
    elif "Animation" == msg_type:
        await bot.send_animation(message.chat.id, file)
    elif "Sticker" == msg_type:
        await bot.send_sticker(message.chat.id, file)
    elif "Voice" == msg_type:
        await bot.send_voice(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, progress=progress, progress_args=[message, "up"])
    elif "Audio" == msg_type:
        try:
            thumb = await acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            thumb = None
        await bot.send_audio(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)
    elif "Photo" == msg_type:
        await bot.send_photo(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities)

    os.remove(file)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    await bot.delete_messages(message.chat.id, [smsg.id])

# Get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    try:
        msg.photo
        return "Photo"
    except:
        pass
    return "Text"

bot.run()
