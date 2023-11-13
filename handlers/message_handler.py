import logging

from telegram import Update, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import CallbackContext

import handlers.keyboard_handler as kb
import handlers.state_handler as sh
from api.google_maps import (
    Distance,
    get_location,
    get_photo,
    haversine
)

import handlers.state_handler as sh
import handlers.keyboard_handler as kb
from telegram import InputMediaPhoto

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

    # This needs to be replaces by STATE machine in the future
    if context.user_data.get("play_again", False):
        msg_type = 2
        context.user_data['play_again'] = False
        
    lat = message["location"]["latitude"]
    long = message["location"]["longitude"]
    print(lat, long, "before starting")
    
    user_state = sh.get_user_state(context.user_data)

    if msg_type == 0 and user_state == sh.StateStages.ASKING_LIVE_LOCATION:
        # receiving a single (non-live) location
        logger.info(
            f"= Got Single (non-live) location {message['location']} on chat #{chat_id}"
        )
        context.bot.send_message(chat_id, "⚠️ Wrong Location Sent ⚠️\nWoops. You've sent us a location, "
                                          "but not your Live Location!\nPlease activate your Live Location instead!")
    elif msg_type == 1:
        # live location ended
        live_location_timeout(update, context, chat_id, user_state)
    elif msg_type == 2:
        # got live location for the first time
        first_decide_on_place(update, context, chat_id, lat, long)
        ###context.user_data['msg'] = context.bot.send_message(chat_id=chat_id, text="Start moving !!!")
        ###context.user_data['not_moving_msg'] = None
    elif msg_type == 3 and user_state == sh.StateStages.PLAYING_LOOP:
        # We get an updated location from the user sharing his live location
        playing_loop(update, context, message)


def live_location_timeout(update, context, chat_id, user_state):
    logger.info(f"= Live location paused. Chat ID: #{chat_id}")
    context.bot.send_message(chat_id, "⚠️ Live Location Lost ⚠️\n\nOh no, we can no longer find you! 😬")
    context.bot.send_message(chat_id, "Please activate your Live Location to continue.")
    if user_state == sh.StateStages.LOCATION_SELECTION_LOOP:
        kb.button(update, context)
    elif user_state == sh.StateStages.PLAYING_LOOP:
        sh.set_user_state(context.user_data, sh.StateStages.PAUSED)


def playing_loop(update, context, message):
    chat_id = update.effective_chat.id
    old_location = 0
    try:
        old_location = context.user_data["current_location"]
    except KeyError:
        old_location = 0
    context.user_data["current_location"] = {'latitude': message["location"]["latitude"],
                                             'longitude': message["location"]["longitude"]}
    logger.info(
        f"= Live location received: {message['location']}. Chat ID: #{chat_id}"
    )
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

        if old_location != 0 and abs(current_distance - old_distance) < 2:
            context.bot.send_message(chat_id, f"Feeling lost? 🤔\nIt seems like you haven't moved!\n")
        elif old_location != 0 and current_distance < old_distance:
            context.bot.send_message(chat_id, f"🔥🔥🔥 Getting hotter 🔥🔥🔥\n you are {current_distance}"
                                              f"meters from your destination!")
            
        elif old_location != 0 and current_distance <= 20:
            play_again_keyboard = [[
                InlineKeyboardButton("Hell Yeah!", callback_data="play_yes"),
                InlineKeyboardButton("No, Leave Me Alone", callback_data="play_no"),
            ]]
            context.bot.send_message(chat_id, f"🏆🏆🏆 Congratulations! 🏆🏆🏆\n"
                                              f"You have arrived at your destination!\n"
                                              f"Turn turn off your Live Location")
            context.bot.send_message(chat_id, f"Ready for another round? 😉",
                                     reply_markup=InlineKeyboardMarkup(play_again_keyboard))
            context.user_data['play_again'] = True

        elif old_location != 0:
            if context.user_data['not_moving_msg']:
                context.bot.delete_message(chat_id=chat_id,
                                           message_id=context.user_data['not_moving_msg'].message_id)
                context.user_data['not_moving_msg'] = None
            context.bot.edit_message_text(chat_id=chat_id, text=f"🥶🥶🥶 Getting colder 🥶🥶🥶\n you are {current_distance}"
                                                                f"meters from your destination",
                                          message_id=context.user_data['msg'].message_id)

    except KeyError:
        started = False
        return

    # updating the user with his distance from location
    context.bot.send_message(chat_id,
                             f"Your current distance from\n{context.user_data['destination']['result']['name']}\n"
                             f"is {current_distance} meters")


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
        context.user_data['destination'] = get_location(*context.user_data['distance'].get_destination(), filter=None, data=context.user_data)

        # Keeping the location of our destination in user_data
        context.user_data['destination_location'] = context.user_data['destination']['result']['geometry']['location']

        try:
            photo_reference = context.user_data['destination']['result']['photos'][0]['photo_reference']
            image_exists = True
        except (IndexError, KeyError):
            image_exists = False

def first_decide_on_place(update, context, chat_id, lat, long):
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
                             f"Looks familiar? 🧐\n\nYour mission: Observe the photo above and try to "
                             f"get there without using a map 🚫🗺")
    choice_keyboard = [[
        InlineKeyboardButton("accept", callback_data="accept"),
        InlineKeyboardButton("choose another", callback_data=f"another,{lat},{long}"),
    ]]

    context.bot.send_message(
        chat_id=chat_id,

        text="Do you accept the current challenge?! or would you rather have a different one?",
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

