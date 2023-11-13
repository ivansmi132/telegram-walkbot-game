import logging
from telegram.ext import CallbackContext
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from bot_settings import MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME


import handlers.state_handler as sh
import handlers.database_handler as db
import os

# from bot import db_handler


# Import the logger from the main module
logger = logging.getLogger(__name__)

# Create mongo handler instance
db_handler = db.MongoDBHandler(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)


def start(update: Update, context: CallbackContext):
    sh.set_user_state(context.user_data, sh.StateStages.ASKING_DISTANCE)
    chat_id = update.effective_chat.id
    user_name = update.message.chat.first_name
    logger.info(f"> Start chat #{chat_id}, with: {user_name!r}")

    # Message #1: A lively welcome
    context.bot.send_message(
        chat_id=chat_id,
        text="Welcome aboard, fearless explorer!\nGet ready to embark on an epic journey! 🚀",
        reply_markup=ReplyKeyboardRemove()
    )

    # Message #2: Choose your distance
    distance_keyboard = [[
        InlineKeyboardButton("1km", callback_data="1"),
        InlineKeyboardButton("2km", callback_data="2"),
        InlineKeyboardButton("3km", callback_data="3"),
        InlineKeyboardButton("4km", callback_data="4"),
        InlineKeyboardButton("5km", callback_data="5"),
    ]]

    context.bot.send_message(
        chat_id=chat_id,

        text="I'm your adventure companion \ntogether, we'll uncover hidden gems and thrilling locations 🗺️\n\n"
             "But how far are you willing to travel for your next adventure?",
        reply_markup=InlineKeyboardMarkup(distance_keyboard)
    )

    logger.info(f"> Requesting user to select desired distance. Chat ID: #{chat_id}")


def score(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_score = db_handler.find_score(chat_id)
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Your score is: {user_score}!"
    )


def leaderboard(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    scores = db_handler.find_top_three()
    text = ""
    if len(scores) > 0:
        text += f"🥇 {scores[0][0]}, score: {scores[0][1]}!\n"
    if len(scores) > 1:
        text += f"🥈 {scores[1][0]}, score: {scores[1][1]}!\n"
    if len(scores) > 2:
        text += f"🥉 {scores[2][0]}, score: {scores[2][1]}!\n"
    context.bot.send_message(
        chat_id=chat_id,
        text=text
    )

def finish(update: Update, context: CallbackContext):

    pass
