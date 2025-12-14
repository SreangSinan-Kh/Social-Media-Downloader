import telebot
from telebot import types
import yt_dlp
import os
import time
import threading
from flask import Flask # ថែមថ្មីសម្រាប់ Render
from threading import Thread # ថែមថ្មី

# --- CONFIGURATION ---
BOT_TOKEN = '8413248700:AAFUkOJREwWs3YQ0ROielTXTYvGJ9xa3RLk' # ⚠️ ដាក់ Token បង
MAX_FILE_SIZE = 49 * 1024 * 1024 

bot = telebot.TeleBot(BOT_TOKEN)
user_links = {}

# --- WEB SERVER សម្រាប់ RENDER & UPTIMEROBOT (ថែមថ្មី) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running! (Sreang Sinan)"

def run_http():
    # Render ត្រូវការ Port 0.0.0.0
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- CODE ដើមនៅដដែល ---

try:
    bot_info = bot.get_me()
    BOT_USERNAME = bot_info.username
    BOT_LINK = f"https://t.me/{BOT_USERNAME}"
except:
    BOT_LINK = "https://t.me/sreangsinan"

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton('▶️ ចាប់ផ្តើម'), types.KeyboardButton('🆘 របៀបប្រើ'))
    markup.add(types.KeyboardButton('📞 ទំនាក់ទំនង'), types.KeyboardButton('ℹ️ អំពី Bot'))
    return markup

def action_menu():
    markup = types.InlineKeyboardMarkup()
    btn_video = types.InlineKeyboardButton("🎬 Video (HD)", callback_data="video")
    btn_audio = types.InlineKeyboardButton("🎵 Audio (Music)", callback_data="audio")
    btn_cancel = types.InlineKeyboardButton("❌ បោះបង់", callback_data="cancel")
    markup.row(btn_video, btn_audio)
    markup.add(btn_cancel)
    return markup

def get_platform_name(url):
    if "tiktok" in url: return "TikTok 🎵"
    if "facebook" in url or "fb.watch" in url: return "Facebook 📘"
    if "instagram" in url: return "Instagram 📸"
    if "youtube" in url or "youtu.be" in url: return "YouTube ▶️"
    return "Social Media 🌐"

def download_media(url, is_audio_only=False):
    timestamp = int(time.time())
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    ydl_opts = {
        'format': 'bestaudio/best' if is_audio_only else 'best[height<=720][ext=mp4]/best[height<=720]/best',
        'outtmpl': f'downloads/file_{timestamp}.%(ext)s',
        'quiet': True, 'no_warnings': True, 'geo_bypass': True, 'nocheckcertificate': True,
        'http_headers': headers,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Media File')
            return filename, title
    except Exception as e:
        print(f"DL Error: {e}")
        return None, None

def process_background(chat_id, message_id, url, is_audio):
    try:
        platform = get_platform_name(url)
        type_str = "Audio 🎧" if is_audio else "Video 🎬"
        bot.edit_message_text(f"⏳ កំពុងទាញយក **{type_str}** ពី **{platform}**...\nសូមរង់ចាំបន្តិច...", chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
        file_path, title = download_media(url, is_audio_only=is_audio)

        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                bot.edit_message_text(f"❌ ឯកសារធំពេក! ({file_size/1024/1024:.1f} MB)\nTelegram Bot ទទួលត្រឹម 50MB។", chat_id=chat_id, message_id=message_id)
                os.remove(file_path)
                return

            bot.edit_message_text(f"🚀 កំពុង Upload **{title}**...", chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
            with open(file_path, 'rb') as file:
                caption = (
                    f"✅ {title}\n"
                    f"🌍 Source: {platform}\n\n"
                    f"🤖 [Downloaded by Telegram bot]({BOT_LINK})"
                )
                if is_audio:
                    bot.send_audio(chat_id, file, caption=caption, parse_mode='Markdown', timeout=120)
                else:
                    bot.send_video(chat_id, file, caption=caption, parse_mode='Markdown', timeout=120)
            bot.delete_message(chat_id, message_id)
            if os.path.exists(file_path): os.remove(file_path)
        else:
            bot.edit_message_text("❌ Download បរាជ័យ! (Link ខូច ឬ Private)", chat_id=chat_id, message_id=message_id)
    except Exception as e:
        try: bot.edit_message_text("❌ មានបញ្ហាបច្ចេកទេស។", chat_id=chat_id, message_id=message_id)
        except: pass

def welcome_logic(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    full_name = f"{first_name} {last_name}" if last_name else first_name

    welcome_text = (
        f"👋 **សួស្តីបង {full_name}!**\n"
        "✨ **ស្វាគមន៍មកកាន់ Social Downloader** ✨\n\n"
        "ខ្ញុំអាចជួយបងទាញយកវីដេអូបានយ៉ាងងាយស្រួលពី៖\n"
        "🔹 **TikTok** (No Watermark)\n"
        "🔹 **Facebook** & **Instagram**\n"
        "🔹 **YouTube** (Video & Audio)\n"
        "🔹 **Other**...................\n\n"
        "🚀 **របៀបប្រើ៖** គ្រាន់តែ **Copy Link** ហើយផ្ញើមកខ្ញុំជាការស្រេច!\n\n"
        "👇 **សូមប្រើប្រាស់ Menu ខាងក្រោមសម្រាប់ជំនួយ៖**"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown', reply_markup=main_menu())

@bot.message_handler(commands=['start'])
def send_welcome(message): welcome_logic(message)

@bot.message_handler(func=lambda msg: msg.text == '▶️ ចាប់ផ្តើម')
def start_btn(message): welcome_logic(message)

@bot.message_handler(func=lambda msg: msg.text == '🆘 របៀបប្រើ')
def help_btn(msg):
    bot.reply_to(msg, "📖 **របៀបប្រើប្រាស់៖**\n1️⃣ Copy Link វីដេអូ\n2️⃣ Paste ចូលក្នុង Bot នេះ\n3️⃣ ជ្រើសរើស Video ឬ Audio\n✅ រួចរាល់!", parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == '📞 ទំនាក់ទំនង')
def contact_btn(msg):
    text = (
        "📞 **ព័ត៌មានទំនាក់ទំនង៖**\n\n"
        "👤 **Mr. Sreang Sinan**\n"
        "📱 Tel: `087533780`\n"
        "🔹 តេលេក្រាម: [ចុចទីនេះ](https://t.me/sreangsinan)"
    )
    bot.reply_to(msg, text, parse_mode='Markdown')

@bot.message_handler(func=lambda msg: msg.text == 'ℹ️ អំពី Bot')
def about_btn(msg):
    bot.reply_to(msg, "🤖 **Social Downloader**\nVersion 13.0 (Render Ready)")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    if url.startswith(('http://', 'https://')):
        user_links[message.chat.id] = url
        platform = get_platform_name(url)
        bot.reply_to(message, f"🔎 ឃើញ Link **{platform}**!\n👇 តើបងចង់បានទម្រង់មួយណា?", parse_mode='Markdown', reply_markup=action_menu())
    else:
        bot.reply_to(message, "⚠️ សូមផ្ញើ Link ឱ្យត្រឹមត្រូវ។", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    if call.data == "cancel":
        bot.delete_message(chat_id, call.message.message_id)
        return
    url = user_links.get(chat_id)
    if not url:
        bot.answer_callback_query(call.id, "Link ផុតកំណត់។")
        return
    threading.Thread(target=process_background, args=(chat_id, call.message.message_id, url, call.data == "audio")).start()

# --- RUNNING BOTH FLASK AND BOT ---
print("Bot is running on Render...")
keep_alive() # បើក Web Server
bot.infinity_polling(timeout=10, long_polling_timeout=5)