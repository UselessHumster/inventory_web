import os

from telebot import TeleBot

bot = TeleBot(os.getenv('TG_BOT_KEY'))

inventory_chat_id = os.getenv('TG_INVENTORY_CHAT')
