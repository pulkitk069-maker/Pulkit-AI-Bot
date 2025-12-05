import telebot
import time
import os
import random
from threading import Thread
from flask import Flask
from config import BOT_TOKEN, ADMIN_ID 
from ai_engine import ask_gemini
from utils import contains_bad_words, search_internet, read_pdf_file, create_voice_note, get_youtube_transcript

# --- SETUP ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# --- GLOBAL VARIABLES ---
bot_active = True
current_mood = "Friendly"
total_messages_count = 0  
start_time = time.time()  
blocked_users = []
voice_mode = False 

# --- USER MAPPING (Updated) ---
USER_PERSONALITIES = {
    5049549997: "Owner",    # Pulkit (Boss)
    6154862357: "Princess", # Mahek (Madam Jii) - Added ✅
}

print("🤖 Pulkit AI (Telegram Version) is Live!")

# --- FLASK SERVER ---
@app.route('/')
def home():
    return "Pulkit AI is Running! 🚀"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- 1. START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Main Pulkit AI hu. 🤖\n\nFeatures:\n📸 Photo bhejo -> Main dekhunga\n🎤 Voice bhejo -> Main sununga\n📄 PDF bhejo -> Main padhunga\n📺 YouTube Link -> Main summary dunga\n🌐 /search -> Internet search")

# --- 2. SUPER ADMIN COMMANDS ---
@bot.message_handler(commands=['sleep', 'wake', 'mood', 'stats', 'status', 'wipe', 'say', 'block', 'voice', 'search'])
def handle_admin(message):
    global bot_active, current_mood, total_messages_count, blocked_users, voice_mode
    
    command = message.text.split()[0]
    
    # --- PUBLIC COMMANDS ---
    if command == "/search":
        query = message.text.replace("/search", "").strip()
        if query:
            bot.send_chat_action(message.chat.id, 'typing')
            results = search_internet(query)
            if results:
                reply = ask_gemini(f"Search Results: {results}\nUser Question: {query}", message.from_user.id, message.from_user.first_name, current_mood)
                bot.reply_to(message, reply)
            else:
                bot.reply_to(message, "Internet par kuch nahi mila. 🤷‍♂️")
        else:
            bot.reply_to(message, "Likh kar bhejo: /search IPL Score")
        return

    # --- ADMIN CHECK (ID Based) ---
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Sorry, tum mere boss nahi ho! 🔒")
        return
    
    # --- ADMIN ACTIONS ---
    if command == "/sleep":
        bot_active = False
        bot.reply_to(message, "😴 Sone ja raha hu.")
    elif command == "/wake":
        bot_active = True
        bot.reply_to(message, "🌞 Awake!")
    elif command == "/stats" or command == "/status":
        uptime = int(time.time() - start_time)
        status = "Online ✅" if bot_active else "Sleeping 💤"
        v_status = "ON 🗣️" if voice_mode else "OFF 📝"
        bot.reply_to(message, f"📊 **Stats:**\nStatus: {status}\nVoice: {v_status}\nMsgs: {total_messages_count}\nUptime: {uptime}s")
    elif command == "/voice":
        if "on" in message.text.lower():
            voice_mode = True
            bot.reply_to(message, "🗣️ Voice Mode: ON")
        else:
            voice_mode = False
            bot.reply_to(message, "📝 Voice Mode: OFF")
    elif command == "/mood":
        try:
            current_mood = message.text.split()[1].capitalize()
            bot.reply_to(message, f"Mood: {current_mood} 😎")
        except:
            bot.reply_to(message, "Use: /mood friendly")
    elif command == "/wipe":
        bot.reply_to(message, "🧠 Memory wiped!")
    elif command == "/say":
        try:
            bot.send_message(message.chat.id, message.text.replace("/say", ""))
        except: pass
    elif command == "/block":
        if message.reply_to_message:
            blocked_users.append(message.reply_to_message.from_user.id)
            bot.reply_to(message, "🚫 Blocked.")

# --- 3. MAIN HANDLER ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'voice', 'document'])
def handle_all_messages(message):
    global bot_active, current_mood, total_messages_count

    if not bot_active: return 
    if message.from_user.id in blocked_users: return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # ID Print (Optional: Rakh sakte ho check karne ke liye)
    # print(f"ID CHECK: {user_id} | Name: {user_name}")

    if user_id in USER_PERSONALITIES:
        active_mood = USER_PERSONALITIES[user_id]
    else:
        active_mood = current_mood

    total_messages_count += 1
    bot.send_chat_action(message.chat.id, 'typing')
    
    media_info = None
    extra_context = None 
    text_prompt = ""

    # PDF
    if message.content_type == 'document' and message.document.mime_type == 'application/pdf':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            pdf_name = f"temp_pdf_{user_id}.pdf"
            with open(pdf_name, 'wb') as f: f.write(downloaded_file)
            extra_context = f"PDF CONTENT:\n{read_pdf_file(pdf_name)}"
            text_prompt = "Is PDF ko summarize karo."
            os.remove(pdf_name)
        except: pass

    # PHOTO
    elif message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = f"temp_img_{user_id}.jpg"
            with open(file_name, 'wb') as f: f.write(downloaded_file)
            media_info = {'path': file_name, 'type': 'image'}
            text_prompt = message.caption if message.caption else "Is photo ko dekho"
        except: pass

    # VOICE
    elif message.content_type == 'voice':
        try:
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = f"temp_audio_{user_id}.ogg"
            with open(file_name, 'wb') as f: f.write(downloaded_file)
            media_info = {'path': file_name, 'type': 'audio'}
            text_prompt = "Reply to audio"
        except: pass

    # TEXT
    elif message.content_type == 'text':
        text_prompt = message.text
        if contains_bad_words(text_prompt):
            bot.reply_to(message, "Mind your language! 🚫")
            return
        
        # YouTube
        if "youtube.com" in text_prompt or "youtu.be" in text_prompt:
            transcript = get_youtube_transcript(text_prompt)
            if transcript: extra_context = f"YOUTUBE:\n{transcript}"
        
        # Search
        triggers = ["latest", "news", "score", "price", "weather", "kab", "kya chal raha"]
        if any(t in text_prompt.lower() for t in triggers):
            bot.send_chat_action(message.chat.id, 'typing')
            search_data = search_internet(text_prompt)
            if search_data: extra_context = f"INTERNET SEARCH:\n{search_data}"

    # AI PROCESS
    time.sleep(random.randint(2, 4))
    ai_reply = ask_gemini(text_prompt, user_id, user_name, active_mood, media_info, extra_context)
    
    # REPLY
    if voice_mode:
        bot.send_chat_action(message.chat.id, 'record_audio')
        audio_file = f"reply_{user_id}.mp3"
        if create_voice_note(ai_reply, audio_file):
            with open(audio_file, 'rb') as audio: bot.send_voice(message.chat.id, audio)
            os.remove(audio_file)
        else:
            bot.reply_to(message, ai_reply) 
    else:
        bot.reply_to(message, ai_reply)

    if media_info:
        try: os.remove(media_info['path'])
        except: pass

# --- START ---
keep_alive() 
bot.infinity_polling()
