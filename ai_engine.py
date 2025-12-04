import google.generativeai as genai
import os
import PIL.Image 
from config import GEMINI_API_KEY, BOT_NAME, DEFAULT_MOOD
from collections import deque
from utils import get_time_greeting
from datetime import datetime

genai.configure(api_key=GEMINI_API_KEY)

# --- MEMORY ---
user_memory = {} 
MEMORY_LIMIT = 15 

def get_system_instruction(mood, user_name):
    greeting = get_time_greeting()
    current_time = datetime.now().strftime('%H:%M')
    
    base_instruction = f"""
    {greeting}, Tera naam {BOT_NAME} hai. 
    Current Time: {current_time}.
    User ka naam {user_name} hai.
    
    --- SPECIAL ABILITIES ---
    1. TRANSLATOR: Agar user '/tr' likhe, to text ko translate karo.
    2. QUIZ MASTER: Agar user '/quiz [topic]' likhe, to uska interview lo.
    3. CODE HELPER: Agar code mile, to error fix karo.
    """
    
    if mood.lower() == "owner":
        return base_instruction + " Tumhara owner **Pulkit** hai. Use 'Boss' ya 'Sir' kaho. Respectful raho."
    elif mood.lower() == "princess":
        return base_instruction + " User **Mahek** (Madam Jii) hain. Unhein 'My Princess' ya 'Madam Jii' bulao. Tone romantic aur caring rakho."
    elif mood.lower() == "friendly":
        return base_instruction + " Tu user ke dost ho. Hinglish mein baat karo."
    elif mood.lower() == "flirty":
        return base_instruction + " Tu flirty hai. Tareef kar aur emojis use kar 😉."
    elif mood.lower() == "roast":
        return base_instruction + " Tu user ko halka roast kar (mazak uda) lekin gaali mat dena."
    
    return base_instruction + " Formal aur polite reh."

# Updated to accept extra_context
def ask_gemini(text_message, user_id, user_name="User", mood=DEFAULT_MOOD, media_file=None, extra_context=None):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = deque(maxlen=MEMORY_LIMIT)
        
        history_context = "\n".join([f"{role}: {msg}" for role, msg in user_memory[user_id]])
        sys_inst = get_system_instruction(mood, user_name)
        
        model = genai.GenerativeModel('gemini-2.5-flash') 
        
        content_input = []
        
        prompt_text = f"System: {sys_inst}\nChat History: {history_context}\n"
        
        # Search/PDF/YouTube Data Yahan Judega
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
