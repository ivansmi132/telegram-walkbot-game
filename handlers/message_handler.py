import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from api.google_maps import (
    Distance,
    get_location,
    get_photo,
    haversine
)
import handlers.state_handler as sh
import handlers.keyboard_handler as kb

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

    user_state = sh.get_user_state(context.user_data)

    if msg_type == 0 and user_state == sh.StateStages.ASKING_LIVE_LOCATION:
        # receiving a single (non-live) location
        logger.info(
            f"= Got Single (non-live) location {message['location']} on chat #{chat_id}"
        )
        context.bot.send_message(chat_id, "You've sent a (non-life) location!\nPlease send a live location instead!")
    elif msg_type == 1:
        # live location ended
        live_location_timeout(update, context, chat_id, user_state)
    elif msg_type == 2:
        # At this point the user started sharing his live location ((this needs to be changed eventually so that it calls the loop for people to choose options))/////////////////////////////

        if user_state == sh.StateStages.PAUSED:
            context.bot.send_message(chat_id, "Thanks for re-sending the live-location, game unpaused!")

        if not user_state == sh.StateStages.ASKING_LIVE_LOCATION:
            context.bot.send_message(chat_id, "Sorry but there is no reason to share your live-location yet.")

        origin = (message["location"]["latitude"], message["location"]["longitude"])  # current location

        # creating a Distance object for the user that will mainly be used to do various distance calculations
        context.user_data["distance"] = Distance(origin, context.user_data["key_name"])
        logger.info(
            f"= Start of live period: Got location {message['location']} on chat #{chat_id}"
        )

        # informing the user of his destination pick, can be omitted later
        context.bot.send_message(chat_id,
                                 f"You have chosen to walk for {context.user_data['distance'].distance}km")

        # context.user_data['distance'].destination is the randomly generated location at the distance the user
        # specified. It's a dictionary of which the 'result' key holds the information of the random place
        context.user_data['destination'] = get_location(*context.user_data['distance'].destination)

        # keeping the location of our destination in user_data
        context.user_data['destination_location'] = context.user_data['destination']['result']['geometry']['location']

        # The initial distance is derived by a haversine function
        initial_distance = int((context.user_data['distance'].current_distance_origin(
            context.user_data['destination_location']['lat'], context.user_data['destination_location']['lng'])) * 1000)
        location_name = context.user_data['destination']['result']['name']

        logger.info(f"Informing chat #{chat_id} of location {location_name}, distance {initial_distance}")

        # informing the user
        context.bot.send_message(chat_id,
                                 f"You will be going to:\n{location_name}\n"
                                 f"{context.user_data['destination']['result']['formatted_address']}\n"
                                 f"Your current distance from there is:\n"
                                 f"{initial_distance} meters")

        # assuming that photos are not always present, might be unnecessary, and have to test this better later
        try:
            photo_reference = context.user_data['destination']['result']['photos'][0]['photo_reference']
            photo_url = get_photo(photo_reference)
            context.bot.sendPhoto(chat_id=chat_id, photo=photo_url)
            logger.info(f"On chat #{chat_id} Sent a photo of {location_name}")
        except IndexError:
            logger.info(f"For chat #{chat_id} there are no photos of {location_name}")
            return

    elif msg_type == 3 and user_state == sh.StateStages.PLAYING_LOOP:
        # We get an updated location from the user sharing his live location
        playing_loop(update, context, message)


def live_location_timeout(update, context, chat_id, user_state):
    logger.info(f"= Live location paused. Chat ID: #{chat_id}")
    context.bot.send_message(chat_id, "Please Re-send Live Location!")
    if user_state == sh.StateStages.LOCATION_SELECTION_LOOP:
        kb.button(update, context)
    elif user_state == sh.StateStages.PLAYING_LOOP:
        sh.set_user_state(context.user_data, sh.StateStages.PAUSED)


def playing_loop(update, context, message):
    chat_id = update.effective_chat.id
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
    except KeyError:
        started = False
        return

    # updating the user with his distance from location
    context.bot.send_message(chat_id,
                             f"Your current distance from\n{context.user_data['destination']['result']['name']}\n"
                             f"is {current_distance} meters")