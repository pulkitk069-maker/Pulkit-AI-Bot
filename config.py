import os
from dotenv import load_dotenv

# Local testing ke liye .env file load karega (agar hai to)
load_dotenv()

# --- SECURE KEYS (Environment Variables se lega) ---

# 1. Telegram Bot Token
# GitHub par upload karte waqt yahan keys mat likhna!
# Render ki settings mein 'BOT_TOKEN' naam se key dalenge.
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Admin Username
# Agar env mein nahi mila to default 'Suspicious_0ne' lega
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Suspicious_0ne")

# 4. Settings
BOT_NAME = "Pulkit AI"
DEFAULT_MOOD = "Friendly"

# 5. Bad Words List
BAD_WORDS = ["pagal", "bevkuf", "stupid", "idiot", "kharab", "bura"]
