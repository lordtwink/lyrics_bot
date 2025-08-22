import os
from dotenv import load_dotenv

load_dotenv()

# Токен Telegram бота
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')