# ai_utils.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

ai_model = None # Default to None

if not GOOGLE_API_KEY:
    print("⚠️ Google API Key not found. AI features will be disabled.")
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        ai_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("✅ Gemini AI Model configured successfully.")
    except Exception as e:
        print(f"❌ Failed to configure Gemini AI Model: {e}")