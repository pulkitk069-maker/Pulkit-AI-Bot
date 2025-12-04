import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- SECURE KEYS (Render se lega) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Suspicious_0ne")

# --- SETTINGS ---
BOT_NAME = "Pulkit AI"
DEFAULT_MOOD = "Friendly"

# --- BAD WORDS LIST (Ye Missing thi!) ---
BAD_WORDS = ["pagal", "bevkuf", "stupid", "idiot", "kharab", "bura", "madarchod", "bhenchod"]
