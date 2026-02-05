import os

from telebot import TeleBot

bot = TeleBot(os.getenv('TG_BOT_KEY'))

admin_chat = os.getenv('TG_INVENTORY_CHAT')
