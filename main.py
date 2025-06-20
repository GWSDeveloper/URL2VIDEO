import telebot
from telebot import types
import yt_dlp
import os
import datetime
import time
from urllib.parse import urlparse

bot_token = '8169381494:AAECSLAqxbpTw44aafLFe7Wy7CMrzKmCFtY'
channel_username = '@FAST_Developers_Official'
max_filesize = 50 * 1024 * 1024  # 50MB
output_folder = "downloads"

bot = telebot.TeleBot(bot_token)
active_downloads = {}  # For /cancel

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

last_edited = {}

def youtube_url_validation(url):
    return url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/")

def is_user_joined(message):
    try:
        status = bot.get_chat_member(chat_id=channel_username, user_id=message.from_user.id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"👋 Hello {message.from_user.first_name}!\n\nSend any YouTube link and choose whether you want to download 🎵 Audio or 📹 Video.\n\n⚠️ Please make sure you've joined {channel_username} to use this bot.")

@bot.message_handler(commands=['cancel'])
def cancel_download(message):
    chat_id = message.chat.id
    if active_downloads.get(chat_id):
        active_downloads[chat_id]["cancel"] = True
        bot.reply_to(message, "❌ Download cancelled.")
    else:
        bot.reply_to(message, "⚠️ No active download found.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    if not is_user_joined(message):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_username[1:]}"))
        bot.reply_to(message, "🚫 Please join our channel to use this bot.", reply_markup=markup)
        return

    url = message.text.strip()
    if not youtube_url_validation(url):
        bot.reply_to(message, "⚠️ Invalid YouTube URL.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎵 Audio", callback_data=f"audio|{url}"),
        types.InlineKeyboardButton("📹 Video", callback_data=f"video|{url}")
    )
    bot.reply_to(message, "🎯 Select the format you want to download:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    format_type, url = call.data.split("|")
    audio = True if format_type == "audio" else False
    download_video(call.message, url, audio=audio)

def download_video(message, url, audio=False, format_id="mp4"):
    chat_id = message.chat.id
    msg = bot.reply_to(message, "📥 Downloading...")

    active_downloads[chat_id] = {"cancel": False}

    def progress_hook(d):
        if active_downloads.get(chat_id, {}).get("cancel"):
            raise Exception("Download cancelled by user")

        if d['status'] == 'downloading':
            try:
                update = False
                key = f"{chat_id}-{msg.message_id}"
                if last_edited.get(key):
                    if (datetime.datetime.now() - last_edited[key]).total_seconds() >= 5:
                        update = True
                else:
                    update = True

                if update:
                    perc = round(d['downloaded_bytes'] * 100 / d['total_bytes'])
                    bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"📥 Downloading: {perc}%")
                    last_edited[key] = datetime.datetime.now()
            except Exception as e:
                print("Progress error:", e)

    video_title = round(time.time() * 1000)
    file_path_template = f'{output_folder}/{video_title}.%(ext)s'

    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': file_path_template,
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if audio else [],
            'max_filesize': max_filesize,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        file_path = info['requested_downloads'][0]['filepath']
        size = os.path.getsize(file_path)
        if size > max_filesize:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"⚠️ File too large. Must be under 50MB.")
            os.remove(file_path)
            return

        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text="📤 Sending file...")

        if audio:
            bot.send_audio(chat_id, open(file_path, 'rb'), reply_to_message_id=message.message_id)
        else:
            width = info['requested_downloads'][0].get('width', 480)
            height = info['requested_downloads'][0].get('height', 360)
            bot.send_video(chat_id, open(file_path, 'rb'), reply_to_message_id=message.message_id, width=width, height=height)

        bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        print("Error:", e)
        bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"❌ Error: {str(e)}")

    finally:
        if chat_id in active_downloads:
            del active_downloads[chat_id]

bot.polling()import os
import telebot
import threading
import yt_dlp
import time
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = "@FAST_Developers_Official"
OUTPUT_DIR = "downloads"
MAX_FILESIZE = 49 * 1024 * 1024  # 49 MB (under Telegram limit)
bot = telebot.TeleBot(BOT_TOKEN)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Active downloads tracking
active_downloads = {}
last_edit = {}

WELCOME_MESSAGE = """
👋 *Welcome to the Ultimate Media Downloader Bot!*

This bot allows you to download *audios only* from:
YouTube, Twitter, TikTok, Reddit & more!

🛠️ *How to Use:*
1. Send a video/audio link.
2. Use `/cancel` to stop any ongoing download.

🔥 *Powered by FAST Developers* 🔥
"""

def is_verified(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "creator", "administrator"]
    except:
        return False

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"),
        InlineKeyboardButton("✅ Verify", callback_data="verify")
    )
    bot.send_message(msg.chat.id, WELCOME_MESSAGE, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "verify")
def snd_verify(c):
    if is_verified(c.from_user.id):
        bot.answer_callback_query(c.id, "✅ Verified!")
        bot.send_message(c.from_user.id, "✅ You're verified! Send a video/audio link.")
    else:
        bot.answer_callback_query(c.id, "❌ Please join first!")

@bot.message_handler(commands=['cancel'])
def cmd_cancel(msg):
    cd = msg.chat.id
    if cd in active_downloads:
        active_downloads[cd]['cancel'] = True
        bot.reply_to(msg, "❌ Canceling download...")
    else:
        bot.reply_to(msg, "ℹ️ No active download to cancel.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def handle_link(msg):
    if not is_verified(msg.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"),
            InlineKeyboardButton("✅ Verify", callback_data="verify")
        )
        bot.reply_to(msg, "❌ You need to join our channel to use this bot.", reply_markup=markup)
        return

    threading.Thread(target=download_audio, args=(msg,)).start()

def download_audio(msg):
    cid = msg.chat.id
    url = msg.text.strip()
    timestamp = str(int(time.time()))
    outtmpl = os.path.join(OUTPUT_DIR, f"{timestamp}.%(ext)s")

    active_downloads[cid] = {'cancel': False}

    def progress(d):
        if active_downloads[cid]['cancel']:
            raise Exception("Canceled")
        if d['status'] == 'downloading':
            key = f"{cid}-{msg.message_id}"
            now = datetime.datetime.now()
            if now - last_edit.get(key, now) >= datetime.timedelta(seconds=3):
                pct = round(d.get('downloaded_bytes',0) * 100 / d.get('total_bytes',1))
                bot.edit_message_text(chat_id=cid, message_id=status_msg.message_id,
                                      text=f"🎧 Downloading... {pct}%")
                last_edit[key] = now

    ydl_opts = {
        'format': 'bestaudio',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'outtmpl': outtmpl,
        'max_filesize': MAX_FILESIZE,
        'progress_hooks': [progress],
        'quiet': True,
    }

    status_msg = bot.reply_to(msg, "🎧 Starting download...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if active_downloads[cid]['cancel']:
            bot.edit_message_text("❌ Download canceled", cid, status_msg.message_id)
            cleanup_files(timestamp)
            return

        final = ydl.prepare_filename(info)
        final = final.rsplit(".",1)[0] + ".mp3"

        bot.edit_message_text("📤 Sending audio...", cid, status_msg.message_id)
        with open(final, 'rb') as f:
            bot.send_audio(cid, f, reply_to_message_id=msg.message_id)

    except Exception as e:
        errmsg = "⚠️ " + str(e)
        bot.edit_message_text(errmsg, cid, status_msg.message_id)
    finally:
        cleanup_files(timestamp)
        active_downloads.pop(cid, None)

def cleanup_files(prefix):
    for fn in os.listdir(OUTPUT_DIR):
        if fn.startswith(prefix):
            os.remove(os.path.join(OUTPUT_DIR, fn))

print("🤖 Bot is up and running!")
bot.infinity_polling()
