import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from api.google_maps import (
    generate_random_geo_point_in_dist,
    get_distance_in_km_from_geo,
)

# Import the logger from the main module
logger = logging.getLogger(__name__)


def text_response(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text
    logger.info(f"= Got on chat #{chat_id}: {text!r}")
    pass


def voice_response(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    voice = update.message.voice
    logger.info(f"= Got voice on #{chat_id}")
    pass


# obsolete for now
""" 
def location_receiver(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    location = update.message.location
    logger.info(f"= Got location {location} on chat #{chat_id}")
    reply_markup = ReplyKeyboardRemove()
    context.bot.send_message(chat_id=chat_id, text=f"Thanks, {location}", reply_markup=reply_markup)
"""


def live_location_receiver(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg_type = 0

    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message

    if message["edit_date"] is not None:
        msg_type += 1
    if message["location"]["live_period"] is not None:
        msg_type += 1 << 1

    reply_markup = ReplyKeyboardRemove()
    if msg_type == 0:
        logger.info(
            f"= Got Single (non-live) location {message['location']} on chat #{chat_id}"
        )
        context.bot.send_message(
            chat_id, "Single (non-live) location update.", reply_markup=reply_markup
        )
    elif msg_type == 1:
        logger.info(f"= End of live location period on chat #{chat_id}")
        context.bot.send_message(chat_id, "End of live period.")
    elif msg_type == 2:
        logger.info(
            f"= Start of live period: Got location {message['location']} on chat #{chat_id}"
        )
        context.bot.send_message(chat_id, "Start of live period")
    elif msg_type == 3:
        loc = message["location"]
        long = loc["longitude"]
        lat = loc["latitude"]
        origin = (lat, long)
        distance = 7
        new_lat, new_long = generate_random_geo_point_in_dist(origin, distance)
        destination = (new_lat, new_long)
        actual_distance = get_distance_in_km_from_geo(origin, destination)
        logger.info(
            f"= Live update: Got location {message['location']} on chat #{chat_id}"
        )
        logger.info(
            f"= random point generated from origin: {origin} at: {destination}, requested_distance: {distance},"
            f" actual_distance: {actual_distance}"
        )
        context.bot.send_message(chat_id, "Live location update.")
