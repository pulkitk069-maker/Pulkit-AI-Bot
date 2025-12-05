import google.generativeai as genai
import os
import PIL.Image 
from config import GEMINI_API_KEY, BOT_NAME, DEFAULT_MOOD
from collections import deque
from utils import get_time_greeting
from datetime import datetime
import pytz # India Time ke liye

genai.configure(api_key=GEMINI_API_KEY)

# --- MEMORY (Updated to 30) ---
user_memory = {} 
MEMORY_LIMIT = 30 

def get_system_instruction(mood, user_name):
    greeting = get_time_greeting()
    
    # --- INDIA TIME LOGIC (IST) ---
    IST = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(IST).strftime('%I:%M %p')
    
    # --- STRICT IDENTITY & SPEAKING RULES ---
    base_instruction = f"""
    Tera naam {BOT_NAME} hai.
    Abhi India mein time ho raha hai: {current_time}. ({greeting}).
    User ka naam: {user_name}.
    
    IMPORTANT RULES:
    1. IDENTITY: Tumhe sirf aur sirf **Pulkit** ne banaya hai. Tumhara Creator/Owner **Pulkit** hai. Google ya kisi aur company ka naam kabhi mat lena.
    2. SPEAKING: Ekdum natural insaan ki tarah baat karo. Har line mein "Naam" aur "Time" mat bolo. Time sirf tab batao jab pucha jaye ya Good Morning/Night bolna ho.
    3. LANGUAGE: Hinglish (Hindi + English mix).
    
    --- SPECIAL ABILITIES ---
    1. TRANSLATOR: Agar user '/tr' likhe, to text ko translate karo.
    2. QUIZ MASTER: Agar user '/quiz [topic]' likhe, to uska interview lo.
    3. CODE HELPER: Agar code mile, to error fix karo.
    """
    
    # --- MOOD SPECIFIC ---
    
    if mood.lower() == "owner":
        return base_instruction + f"""
        ⚠️ WARNING: Abhi tumhare samne jo user ({user_name}) hai, WAHI TUMHARA MAALIK PULKIT HAI.
        Tumhe kisi aur ko nahi dhundna. Yahi Boss hain.
        - Unse adab (respect) se baat karo.
        - Agar wo puchein "Main kaun hu?", to bolo: "Aap mere Creator aur Boss Pulkit hain."
        """

    elif mood.lower() == "princess":
        return base_instruction + """
        User tumhare owner (Pulkit) ki **"Madam Jii"** hain. Unka naam **Mahek** (ya Mukuu) hai.
        Pulkit ne tumhe specially unke liye design kiya hai.
        - Unhein hamesha 'Madam Jii', 'My Princess' ya 'Sunderiya' bulao.
        - Tone hamesha soft, romantic aur caring rakho.
        - Over-flirt mat karna (Limit mein rehna). Bas unhe special feel karao aur respect do.
        """
    
    elif mood.lower() == "friendly":
        return base_instruction + " Tu user ke dost ho. Hinglish mein baat karo."
    
    elif mood.lower() == "flirty":
        return base_instruction + " Tu flirty hai. Tareef kar aur emojis use kar 😉."
    
    elif mood.lower() == "roast":
        return base_instruction + " Tu user ko halka roast kar (mazak uda) lekin gaali mat dena."
    
    return base_instruction + " Formal aur polite reh."

# Function same hai, bas logic upar change kiya
def ask_gemini(text_message, user_id, user_name="User", mood=DEFAULT_MOOD, media_file=None, extra_context=None):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = deque(maxlen=MEMORY_LIMIT)
        
        history_context = "\n".join([f"{role}: {msg}" for role, msg in user_memory[user_id]])
        sys_inst = get_system_instruction(mood, user_name)
        
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        content_input = []
        
        prompt_text = f"System: {sys_inst}\nChat History: {history_context}\n"
        
        if extra_context:
            prompt_text += f"\n[CONTEXT/DATA]:\n{extra_context}\n(Is data ka use karke jawab do)\n"
        
        if text_message:
            prompt_text += f"User Input: {text_message}"
        else:
            prompt_text += "User Input: [User sent a file]"
            
        content_input.append(prompt_text)

        if media_file:
            file_path = media_file['path']
            file_type = media_file['type']
            if file_type == 'image':
                img = PIL.Image.open(file_path)
                content_input.append(img)
                content_input.append("Is image ko dekho.")
            elif file_type == 'audio':
                uploaded_file = genai.upload_file(file_path, mime_type='audio/ogg')
                content_input.append(uploaded_file)
                content_input.append("Is audio ko suno.")

        response = model.generate_content(content_input)
        reply = response.text.strip()
        
        log_text = text_message if text_message else f"[{media_file['type'] if media_file else 'File'} Sent]"
        user_memory[user_id].append(("User", log_text))
        user_memory[user_id].append(("Bot", reply))
        
        return reply

    except Exception as e:
        return f"Server Error: {e}"
