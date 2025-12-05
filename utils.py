from datetime import datetime
import os
import asyncio
import pytz # India Time ke liye
from config import BAD_WORDS

# --- LIBRARIES ---
import edge_tts
from duckduckgo_search import DDGS
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

# 1. Time Awareness (INDIA TIME) 🇮🇳
def get_time_greeting():
    # India Timezone set kar rahe hain
    IST = pytz.timezone('Asia/Kolkata')
    now_india = datetime.now(IST)
    current_hour = now_india.hour
    
    if 4 <= current_hour < 12: return "Good Morning"
    elif 12 <= current_hour < 17: return "Good Afternoon"
    elif 17 <= current_hour < 21: return "Good Evening"
    else: return "Late Night hai, so jao"

# 2. Bad Word Filter
def contains_bad_words(text):
    text = text.lower()
    for word in BAD_WORDS:
        if word in text: return True
    return False

# 3. INTERNET SEARCH (DuckDuckGo)
def search_internet(query):
    try:
        results = DDGS().text(query, max_results=3)
        if not results: return None
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except Exception as e:
        print(f"Search Error: {e}")
        return None

# 4. PDF READER
def read_pdf_file(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for i, page in enumerate(reader.pages):
            if i > 10: break 
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# 5. TEXT TO SPEECH (Male Voice - Prabhat)
async def _generate_audio(text, output_file):
    voice = "en-IN-PrabhatNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def create_voice_note(text, output_file):
    try:
        asyncio.run(_generate_audio(text, output_file))
        return True
    except Exception as e:
        print(f"Audio Error: {e}")
        return False

# 6. YOUTUBE TRANSCRIPT
def get_youtube_transcript(video_url):
    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1].split("?")[0]
        else:
            return None
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([i['text'] for i in transcript])
        return full_text[:4000] 
    except Exception as e:
        return None

# 7. Cleanup
def cleanup_files(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
