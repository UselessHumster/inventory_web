from .settings import bot

def send_device_creation_to_tg(msg, chat_id):
    return bot.send_message(chat_id=chat_id, text=msg)
