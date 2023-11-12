from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup

# Import the logger from the main module
logger = logging.getLogger(__name__)


def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id

    # Get the callback data
    callback_data = query.data

    # Save the user's selected distance
    context.user_data['selected_distance'] = callback_data

    # Send a message to the user confirming their selection
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Whoah, {callback_data}?! That's going to be an amazing adventure!  🧭"
    )


def button(update, context):
    query = update.callback_query
    val = query.data

    # Store value
    context.user_data["key_name"] = val
    # tell the user it worked
    query.answer("Updated Successfully!")


def location_keyboard_button(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"= Asking for location on chat #{chat_id}")
    location_keyboard = KeyboardButton(text="send_location", request_location=True)
    loc = KeyboardButton.request_location
    custom_keyboard = [[location_keyboard]]
    reply_markup = ReplyKeyboardMarkup(
        custom_keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat_id,
        text="Would you mind sharing your location with me?",
        reply_markup=reply_markup,
    )
