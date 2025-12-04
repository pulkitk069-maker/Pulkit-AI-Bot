import telebot
import time
import os
import random
from threading import Thread
from flask import Flask
# Config se ab ADMIN_ID import kar rahe hain (USERNAME hata diya)
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

# --- USER MAPPING ---
USER_PERSONALITIES = {
    5049549997: "Owner", 
    # Mahek ID example: 1234567890: "Princess"
}

print("🤖 Pulkit AI (Telegram Version) is Live!")

# --- FLASK SERVER (Keep Alive) ---
@app.route('/')
def home():
    return "Pulkit AI is Alive and Running! 🚀"

def run_http():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# --- 1. START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Main Pulkit AI hu. 🤖\n\nFeatures:\n📸 Photo bhejo -> Main dekhunga\n🎤 Voice bhejo -> Main sununga\n📄 PDF bhejo -> Main padhunga\n📺 YouTube Link -> Main summary dunga\n🌐 /search -> Internet search")

# --- 2. SUPER ADMIN COMMANDS (ID BASED) ---
@bot.message_handler(commands=['sleep', 'wake', 'mood', 'stats', 'status', 'wipe', 'say', 'block', 'voice', 'search'])
def handle_admin(message):
    global bot_active, current_mood, total_messages_count, blocked_users, voice_mode
    
    command = message.text.split()[0]
    
    # --- PUBLIC COMMANDS (Search sabke liye hai) ---
    if command == "/search":
        query = message.text.replace("/search", "").strip()
        if query:
            bot.send_chat_action(message.chat.id, 'typing')
            results = search_internet(query)
            if results:
                # AI ko context ke saath bhej rahe hain
                reply = ask_gemini(f"Search Results: {results}\nUser Question: {query}", message.from_user.id, message.from_user.first_name, current_mood)
                bot.reply_to(message, reply)
            else:
                bot.reply_to(message, "Internet par kuch nahi mila. 🤷‍♂️")
        else:
            bot.reply_to(message, "Likh kar bhejo: /search IPL Score")
        return

    # --- ADMIN ONLY CHECK (AB ID SE HOGA) ---
    # Yahan hum check kar rahe hain ki message bhejne wala ADMIN_ID (Aap) hai ya nahi
    # Username check hata diya gaya hai taaki confusion na ho
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Sorry, tum mere boss nahi ho! 🔒")
        return
    
    # --- ADMIN ACTIONS ---
    
    # 1. SLEEP
    if command == "/sleep":
        bot_active = False
        bot.reply_to(message, "😴 Sone ja raha hu. Koi disturb nahi karega.")
        
    # 2. WAKE
    elif command == "/wake":
        bot_active = True
        bot.reply_to(message, "🌞 Good Morning! Main wapas aa gaya.")
        
    # 3. STATS / STATUS
    elif command == "/stats" or command == "/status":
        uptime = int(time.time() - start_time)
        status = "Online ✅" if bot_active else "Sleeping 💤"
        v_status = "ON 🗣️" if voice_mode else "OFF 📝"
        
        stats_msg = (
            f"📊 **Bot Status Report**\n"
            f"--------------------------\n"
            f"🟢 **Status:** {status}\n"
            f"🎭 **Mood:** {current_mood}\n"
            f"🎤 **Voice Mode:** {v_status}\n"
            f"💬 **Total Messages:** {total_messages_count}\n"
            f"⏱️ **Uptime:** {uptime} seconds\n"
            f"🚫 **Blocked:** {len(blocked_users)}"
        )
        bot.reply_to(message, stats_msg, parse_mode="Markdown")

    # 4. VOICE MODE TOGGLE
    elif command == "/voice":
        if "on" in message.text.lower():
            voice_mode = True
            bot.reply_to(message, "🗣️ Voice Mode: ON (Prabhat Active)")
        else:
            voice_mode = False
            bot.reply_to(message, "📝 Voice Mode: OFF (Text reply)")

    # 5. MOOD
    elif command == "/mood":
        try:
            new_mood = message.text.split()[1]
            current_mood = new_mood.capitalize()
            bot.reply_to(message, f"Mood changed to: {current_mood} 😎")
        except:
            bot.reply_to(message, "Usage: /mood [friendly/flirty/roast]")

    # 6. WIPE
    elif command == "/wipe":
        bot.reply_to(message, "🧠 Memory wipe successful. Fresh start!")

    # 7. SAY
    elif command == "/say":
        try:
            text_to_say = message.text.replace("/say", "").strip()
            if text_to_say:
                bot.send_message(message.chat.id, text_to_say)
            else:
                bot.reply_to(message, "Kya bolna hai? Likh kar bhejo.")
        except:
            pass

    # 8. BLOCK
    elif command == "/block":
        if message.reply_to_message:
            b_id = message.reply_to_message.from_user.id
            blocked_users.append(b_id)
            bot.reply_to(message, f"🚫 User {b_id} blocked.")
        else:
            bot.reply_to(message, "Kisi ke message pe reply karke /block likho.")

# --- 3. MAIN MESSAGE HANDLER ---
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'voice', 'document'])
def handle_all_messages(message):
    global bot_active, current_mood, total_messages_count

    if not bot_active: return 
    if message.from_user.id in blocked_users: return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # --- ID DETECTOR (Mahek ke liye - Terminal/Logs mein dikhega) ---
    print(f"ID CHECK: {user_id} | Name: {user_name}")
    # -----------------------------------

    # Mood Logic
    if user_id in USER_PERSONALITIES:
        active_mood = USER_PERSONALITIES[user_id]
    else:
        active_mood = current_mood

    total_messages_count += 1
    bot.send_chat_action(message.chat.id, 'typing')
    
    media_info = None
    extra_context = None 
    text_prompt = ""

    # A. PDF HANDLING 📄
    if message.content_type == 'document':
        if message.document.mime_type == 'application/pdf':
            bot.reply_to(message, "📄 PDF padh raha hu, wait...")
            try:
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                pdf_name = f"temp_pdf_{user_id}.pdf"
                with open(pdf_name, 'wb') as f: f.write(downloaded_file)
                
                pdf_text = read_pdf_file(pdf_name)
                extra_context = f"PDF CONTENT:\n{pdf_text}"
                text_prompt = "Is PDF ko summarize karo."
                os.remove(pdf_name)
            except:
                bot.reply_to(message, "PDF Error.")
                return
        else:
            text_prompt = "User sent a document."

    # B. PHOTO HANDLING 📸
    elif message.content_type == 'photo':
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = f"temp_img_{user_id}.jpg"
            with open(file_name, 'wb') as f: f.write(downloaded_file)
            media_info = {'path': file_name, 'type': 'image'}
            text_prompt = message.caption if message.caption else "Is photo ko dekho"
        except:
            bot.reply_to(message, "Photo Error ❌")
            return

    # C. VOICE MESSAGE 🎤
    elif message.content_type == 'voice':
        try:
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = f"temp_audio_{user_id}.ogg"
            with open(file_name, 'wb') as f: f.write(downloaded_file)
            media_info = {'path': file_name, 'type': 'audio'}
            text_prompt = "User ne voice note bheja hai."
        except:
            bot.reply_to(message, "Audio Error ❌")
            return

    # D. TEXT HANDLING (YouTube & Search Logic)
    elif message.content_type == 'text':
        text_prompt = message.text
        if contains_bad_words(text_prompt):
            bot.reply_to(message, "Mind your language! 🚫")
            return
            
        # YouTube Link Check 📺
        if "youtube.com" in text_prompt or "youtu.be" in text_prompt:
            bot.reply_to(message, "📺 Video dekh raha hu...")
            transcript = get_youtube_transcript(text_prompt)
            if transcript:
                extra_context = f"YOUTUBE VIDEO TRANSCRIPT:\n{transcript}"
                text_prompt += "\n(Is video ki summary batao)"
            else:
                bot.reply_to(message, "Video subtitles nahi mile.")
        
        # Auto Search Trigger (Optional keywords)
        triggers = ["latest", "news", "score", "price", "weather", "kab", "kya chal raha"]
        if any(t in text_prompt.lower() for t in triggers):
            bot.send_chat_action(message.chat.id, 'typing')
            search_data = search_internet(text_prompt)
            if search_data:
                extra_context = f"INTERNET SEARCH RESULTS:\n{search_data}"

    # --- AI GENERATION ---
    # Thoda random delay taaki insaan lage
    time.sleep(random.randint(2, 4))
    
    ai_reply = ask_gemini(text_prompt, user_id, user_name, active_mood, media_info, extra_context)
    
    # --- REPLY (Voice or Text) ---
    if voice_mode:
        bot.send_chat_action(message.chat.id, 'record_audio')
        audio_file = f"reply_{user_id}.mp3"
        # Audio create karne ki koshish karo
        if create_voice_note(ai_reply, audio_file):
            with open(audio_file, 'rb') as audio:
                bot.send_voice(message.chat.id, audio)
            os.remove(audio_file)
        else:
            # Agar audio fail ho jaye to text bhej do
            bot.reply_to(message, ai_reply) 
    else:
        bot.reply_to(message, ai_reply)

    # Cleanup Media
    if media_info:
        try: os.remove(media_info['path'])
        except: pass

# --- START SERVER & BOT ---
keep_alive() # Server start
bot.infinity_polling() # Bot start
