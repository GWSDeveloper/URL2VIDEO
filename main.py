import os
import telebot
import threading
import yt_dlp
import time
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import urlparse

BOT_TOKEN = "8169381494:AAECSLAqxbpTw44aafLFe7Wy7CMrzKmCFtY"
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
        'http_headers': {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.9'
       }
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
