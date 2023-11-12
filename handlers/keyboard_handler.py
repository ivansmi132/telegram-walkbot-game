from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup, ForceReply,
)
import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup

live_gif = '/Users/dean_main/Developer/WebDev/Advanced Python/Hackathon/walkSpotBot/telegram-bot-hackathon-walkspotbot/live.gif'


# Import the logger from the main module
logger = logging.getLogger(__name__)


def button(update: Update, context):
    query = update.callback_query
    val = query.data

    # Store value
    context.user_data["key_name"] = val

    # tell the user it worked
    query.answer(f"🔥 Whoah, {val}km?! That's awesome! 🔥")
    query.edit_message_text(f"Wow! You've selected to travel {val}km.\nLet's start the adventure! 🤩")
    chat_id = update.effective_chat.id
    context.user_data['selected_distance'] = val
    logger.info(f"> User selected to travel {val}km. Chat ID: #{chat_id}")

    context.bot.sendAnimation(
        chat_id=chat_id,
        animation=open(live_gif, 'rb'),
        caption="Now, it's time to activate Live Location!"
    )

    # Once we have live location
    logger.info(f"> Requesting user to share live location. Chat ID: #{chat_id}")
