'''
Loads and exposes application configuration for SmartCal.
Reads API keys and settings from the .env file using python-dotenv.
All services import their credentials from this module.
'''
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SPORTS_API_KEY = os.getenv("SPORTS_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
