import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- SECURE KEYS (Render se lega) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- ADMIN CONFIG (New ID Logic) ---
# Yahan ab hum ID check karenge.
# Agar Render par set nahi hai, to default apki ID lega.
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "5049549997"))
except:
    ADMIN_ID = 5049549997

# --- SETTINGS ---
BOT_NAME = "Pulkit AI"
DEFAULT_MOOD = "Friendly"

# --- BAD WORDS LIST ---
BAD_WORDS = ["pagal", "bevkuf", "stupid", "idiot", "kharab", "bura", "madarchod", "bhenchod"]
