import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import CallbackContext
from datetime import datetime, timedelta

import handlers.keyboard_handler as kb
import handlers.state_handler as sh
from api.google_maps import (
    Distance,
    get_location,
    get_photo,
    haversine
)
from bot_settings import MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME

import handlers.database_handler as db
import handlers.state_handler as sh
import handlers.keyboard_handler as kb
from telegram import InputMediaPhoto

# Import the logger from the main module
logger = logging.getLogger(__name__)

db_handler = db.MongoDBHandler(MONGO_CONNECTION, DATABASE_NAME, COLLECTION_NAME)


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

    lat = message["location"]["latitude"]
    long = message["location"]["longitude"]

    user_state = sh.get_user_state(context.user_data)

    if msg_type == 0 and user_state == sh.StateStages.ASKING_LIVE_LOCATION:
        # receiving a single (non-live) location
        logger.info(
            f"= Got Single (non-live) location {message['location']} on chat #{chat_id}"
        )
        context.bot.send_message(chat_id, "⚠️ Wrong Location Sent ⚠️\nWoops. You've sent us a location, "
                                          "but not your Live Location!\nPlease activate your Live Location instead!")
    elif msg_type == 1 and user_state == sh.StateStages.PLAYING_LOOP:
        # live location ended
        live_location_timeout(update, context, chat_id, user_state)
    elif msg_type == 2:
        # got live location for the first time
        if user_state == sh.StateStages.ASKING_LIVE_LOCATION:
            first_decide_on_place(update, context, chat_id, lat, long)
            context.user_data['not_moving_msg'] = None
        elif user_state == sh.StateStages.PAUSED:
            sh.set_user_state(context.user_data, sh.StateStages.PLAYING_LOOP)
    elif msg_type == 3 and user_state == sh.StateStages.PLAYING_LOOP and once_within_time(context, 10):
        # We get an updated location from the user sharing his live location
        playing_loop(update, context, message)


def once_within_time(context, delta_seconds):
    last_time = context.user_data.get('last_time', None)
    if last_time is None:
        context.user_data['last_time'] = datetime.now()
        return True
    current_time = datetime.now()

    if current_time - last_time >= timedelta(seconds=delta_seconds):
        context.user_data['last_time'] = current_time
        return True
    else:
        return False


def live_location_timeout(update, context, chat_id, user_state):
    logger.info(f"= Live location paused. Chat ID: #{chat_id}")
    context.bot.send_message(chat_id, "⚠️ Live Location Lost ⚠️\n\nAy caramba, we can no longer find you! 😬")
    context.bot.send_message(chat_id, "Please activate your Live Location to continue.")
    if user_state == sh.StateStages.LOCATION_SELECTION_LOOP:
        kb.button(update, context)
    elif user_state == sh.StateStages.PLAYING_LOOP:
        sh.set_user_state(context.user_data, sh.StateStages.PAUSED)


def playing_loop(update, context, message):
    chat_id = update.effective_chat.id
    old_location = context.user_data.get("current_location", 0)

    # Logging
    logger.info(f"= User: {chat_id} just entered playing_loop")

    context.user_data["current_location"] = {'latitude': message["location"]["latitude"],
                                             'longitude': message["location"]["longitude"]}

    try:

        current_distance = int((haversine(context.user_data['destination_location']['lat'],
                                          context.user_data['destination_location']['lng'],
                                          context.user_data['current_location']['latitude'],
                                          context.user_data['current_location']['longitude'])) * 1000)
        if old_location != 0:
            old_distance = int((haversine(context.user_data['destination_location']['lat'],
                                          context.user_data['destination_location']['lng'],
                                          old_location['latitude'],
                                          old_location['longitude'])) * 1000)

        if current_distance <= 20:
            play_again_keyboard = [[
                InlineKeyboardButton("Yalla let's go!", callback_data="play_yes"),
                InlineKeyboardButton("Leave me alone!", callback_data="play_no"),
            ]]
            points = int(context.user_data["walk_amount"])
            points = points if points <= 100 else 100
            #db_handler.score_increment(chat_id, points)
            #total_score = db_handler.find_score(chat_id)

            context.bot.send_message(chat_id, f"🏆🏆🏆 Congratulations! 🏆🏆🏆\n"
                                              #f"You got {points} point. for a total score of {total_score}\n"
                                              f"You have arrived at your destination!\n")
            sh.set_user_state(context.user_data, sh.StateStages.WIN_SCREEN)

            context.bot.send_message(chat_id, f"Ready for another round? 😉",
                                     reply_markup=InlineKeyboardMarkup(play_again_keyboard))
        elif old_location != 0 and abs(current_distance - old_distance) < 2:
            if context.user_data['not_moving_msg'] is None:
                context.user_data['not_moving_msg'] = context.bot.send_message(chat_id,
                                                                               f"Feeling lost? 🤔\nIt seems like you "
                                                                               f"haven't moved!\nAre you taking a nap?")
        elif old_location != 0 and current_distance < old_distance:
            if context.user_data['not_moving_msg']:
                context.bot.delete_message(chat_id=chat_id,
                                           message_id=context.user_data['not_moving_msg'].message_id)
                context.user_data['not_moving_msg'] = None
            try:
                context.bot.edit_message_text(chat_id=chat_id, text=f"🔥🔥🔥 Getting HOTTER 🔥🔥🔥\n you are {current_distance}"
                                                                    f" meters away from your destination!",
                                            message_id=context.user_data['msg'].message_id)
            except error.BadRequest:
                return

        elif old_location != 0:
            if context.user_data['not_moving_msg']:
                context.bot.delete_message(chat_id=chat_id,
                                           message_id=context.user_data['not_moving_msg'].message_id)
                context.user_data['not_moving_msg'] = None
            try:
                context.bot.edit_message_text(chat_id=chat_id, text=f"🥶🥶🥶 Getting COLDER 🥶🥶🥶\n you are {current_distance}"
                                                                 f" meters away from your destination",
                                           message_id=context.user_data['msg'].message_id)
            except error.BadRequest:
                return

    except KeyError:
        started = False
        return

    logger.info(
        f"= Live location received. Chat ID: #{chat_id}. distance: {current_distance}, place: {context.user_data['destination']['result']['name']}"
    )



def set_new_place(context, chat_id, lat, long):
    origin = (lat, long)  # Current location
    image_exists = False
    while not image_exists:

        # Creating a Distance object for the user that will mainly be used to do various distance calculations
        context.user_data["distance"] = Distance(origin, context.user_data["key_name"])
        logger.info(
            f"= Start of live period: Got location {lat}:{long} on chat #{chat_id}"
        )

        # Context.user_data['distance'].destination is the randomly generated location at the distance the user
        # Specified. It's a dictionary of which the 'result' key holds the information of the random place
        context.user_data['destination'] = get_location(*context.user_data['distance'].get_destination(), filter=None,
                                                        data=context.user_data)

        # Keeping the location of our destination in user_data
        context.user_data['destination_location'] = context.user_data['destination']['result']['geometry']['location']

        try:
            photo_reference = context.user_data['destination']['result']['photos'][0]['photo_reference']
            image_exists = True
        except (IndexError, KeyError):
            image_exists = False


def first_decide_on_place(update, context, chat_id, lat, long):
    sh.set_user_state(context.user_data, sh.StateStages.LOCATION_SELECTION_LOOP)
    # set a location
    set_new_place(context, chat_id, lat, long)
    # The initial distance is derived by a haversine function
    initial_distance = int((context.user_data['distance'].current_distance_origin(
        context.user_data['destination_location']['lat'], context.user_data['destination_location']['lng'])) * 1000)
    location_name = context.user_data['destination']['result']['name']

    logger.info(f"Informing chat #{chat_id} of location {location_name}, distance {initial_distance}m")

    # Informing the user
    logger.info(f"User ({chat_id})\nSelected destination: {location_name}\n"
                f"{context.user_data['destination']['result']['formatted_address']}\n"
                f"Total distance from current location: {initial_distance}m")

    # Assuming that photos are not always present, might be unnecessary, and have to test this better later
    try:
        photo_reference = context.user_data['destination']['result']['photos'][0]['photo_reference']
        photo_url = get_photo(photo_reference)
        context.user_data['photo'] = context.bot.sendPhoto(chat_id=chat_id, photo=photo_url)
        logger.info(f"On chat #{chat_id} Sent a photo of {location_name}")

        # We should skip to the next result if no photo is available
    except (IndexError, KeyError):
        logger.info(f"For chat #{chat_id} there are no photos of {location_name}")
        return
    context.bot.send_message(chat_id,
                             f"Looks familiar? 🧐\n\nYour mission:\nObserve the photo above and try to "
                             f"get there without using a map 🚫🗺")
    choice_keyboard = [[
        InlineKeyboardButton("Yalla Let's Go!", callback_data="place_accept"),
        InlineKeyboardButton("Skip Location", callback_data=f"place_another,{lat},{long}"),
    ]]

    context.bot.send_message(
        chat_id=chat_id,

        text="Ready for the challenge? or would you like to skip this one?",
        reply_markup=InlineKeyboardMarkup(choice_keyboard)
    )


def decide_on_place(update, context, chat_id, lat, long):
    # set a location
    set_new_place(context, chat_id, lat, long)
    # The initial distance is derived by a haversine function
    initial_distance = int((context.user_data['distance'].current_distance_origin(
        context.user_data['destination_location']['lat'], context.user_data['destination_location']['lng'])) * 1000)
    location_name = context.user_data['destination']['result']['name']

    logger.info(f"Informing chat #{chat_id} of location {location_name}, distance {initial_distance}m")

    # Informing the user
    logger.info(f"User ({chat_id})\nSelected destination: {location_name}\n"
                f"{context.user_data['destination']['result']['formatted_address']}\n"
                f"Total distance from current location: {initial_distance}m")

    # Assuming that photos are not always present, might be unnecessary, and have to test this better later
    try:
        photo_reference = context.user_data['destination']['result']['photos'][0]['photo_reference']
        photo_url = get_photo(photo_reference)
        photo = context.user_data['photo']
        photo.edit_media(media=InputMediaPhoto(media=photo_url))
        logger.info(f"On chat #{chat_id} Sent a photo of {location_name}")

        # We should skip to the next result if no photo is available
    except (IndexError, KeyError):
        logger.info(f"For chat #{chat_id} there are no photos of {location_name}")
        return
