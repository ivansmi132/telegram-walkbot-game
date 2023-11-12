import logging
from telegram.ext import CallbackContext
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton

# Import the logger from the main module
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"> Start chat #{chat_id}")
    context.bot.send_message(chat_id=chat_id, text="💣 Welcome! 💣")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Share live location", request_location=True)]],
        resize_keyboard=True,
    )
    context.bot.send_message(
        chat_id=chat_id,
        text="Would you like to share your live location?",
        reply_markup=keyboard,
    )


# Create a variable to store the user's selected distance
selected_distance = None


def start2(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    logger.info(f"> Start chat #{chat_id}")

    # Message #1: A lively welcome
    context.bot.send_message(
        chat_id=chat_id,
        text="Welcome aboard, fearless explorer! Get ready to embark on an epic journey! 🌍",
        reply_markup=ReplyKeyboardRemove()
    )

    # Message #2: Choose your distance
    distance_keyboard = [[
        InlineKeyboardButton("1km", callback_data="1km"),
        InlineKeyboardButton("2km", callback_data="2km"),
        InlineKeyboardButton("3km", callback_data="3km"),
        InlineKeyboardButton("4km", callback_data="4km"),
        InlineKeyboardButton("5km", callback_data="5km"),
    ]]

    context.bot.send_message(
        chat_id=chat_id,
        text="I'm your adventure companion, and together, we'll uncover hidden gems and thrilling locations. 🗺️\n\n"
             "Before we begin, would you mind telling me how far are you willing to travel for your next adventure?",
        reply_markup=InlineKeyboardMarkup(distance_keyboard)
    )
    logger.info(f"> Requesting user to select desired distance. Chat ID: #{chat_id}")
