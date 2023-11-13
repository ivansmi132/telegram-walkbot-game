import sys

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup, ForceReply, ReplyKeyboardRemove,
)
import os
import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
import handlers.state_handler as sh

# Import the logger from the main module
logger = logging.getLogger(__name__)


def get_live_gif():
    project_root = os.getcwd()
    live_gif = os.path.join(project_root, "assets/live.gif")
    return live_gif


def button(update: Update, context):
    sh.set_user_state(context.user_data, sh.StateStages.ASKING_LIVE_LOCATION)

    query = update.callback_query
    val = query.data
    reply_markup = ReplyKeyboardRemove()

    # Store value
    context.user_data["key_name"] = int(val)

    # tell the user it worked
    query.answer(f"🔥 Whoah, {val}km?! That's awesome! 🔥")
    query.edit_message_text(f"Wow! You've selected to travel {val}km.\nLet's start the adventure! 🤩")
    chat_id = update.effective_chat.id
    context.user_data['selected_distance'] = val
    logger.info(f"> User selected to travel {val}km. Chat ID: #{chat_id}")

    gif_path = get_live_gif()

    context.bot.sendAnimation(
        chat_id=chat_id,
        animation=open(gif_path, 'rb'),
        caption="Now, it's time to activate Live Location!"
    )

    # Once we have live location
    logger.info(f"> Requesting user to share live location. Chat ID: #{chat_id}")
