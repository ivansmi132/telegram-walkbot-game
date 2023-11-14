import sys
from datetime import time

import telegram
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
from handlers.command_handler import play, start
from handlers.message_handler import decide_on_place
from datetime import datetime, timedelta

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
    context.user_data["key_name"] = int(val[1])
    context.user_data["walk_amount"] = int(val[1])
    # tell the user it worked
    query.answer(f"🔥 Whoah, {val[1]}km?! That's awesome! 🔥")
    query.edit_message_text(f"Wow! You've selected to travel {val[1]}km.\nLet's start the adventure! 🤩")
    chat_id = update.effective_chat.id
    context.user_data['selected_distance'] = val
    logger.info(f"> User selected to travel {val[1]}km. Chat ID: #{chat_id}")

    try:
        gif_path = get_live_gif()

        context.bot.sendAnimation(
            chat_id=chat_id,
            animation=open(gif_path, 'rb'),
            caption=f"{'^' * 30}\nNow, please activate your Live Location!"
        )
    except telegram.error.NetworkError:
        context.bot.send_message(chat_id=chat_id, text="Now, please activate your Live Location!")


    logger.info(f"> Requesting user to activate Live Location. Chat ID: #{chat_id}")


def play_again_button(update: Update, context):
    query = update.callback_query
    val = query.data
    if val == 'play_yes':
        query.edit_message_text("For another round we go!")
        play(update, context)
    else:
        sh.set_user_state(context.user_data, sh.StateStages.BEFORE_START)
        query.edit_message_text("Thank you for playing!\nPlease don't forget to turn off your live location!")


def places_choice_button(update, context):
    chat_id = update.effective_chat.id
    query = update.callback_query
    val = query.data
    val = val.split('_')[1]
    if val == "accept":
        context.user_data['point_timer'] = datetime.now()
        context.user_data['msg'] = context.bot.send_message(chat_id=chat_id, text="Game is staring! 🤩🤩🤩")
        query.edit_message_text("Challenge accepted!")
        sh.set_user_state(context.user_data, sh.StateStages.PLAYING_LOOP)
    else:
        fixed = val.split(',')
        decide_on_place(update, context, chat_id, float(fixed[1]), float(fixed[2]))

