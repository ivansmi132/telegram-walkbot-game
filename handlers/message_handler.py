import logging
from telegram.ext import CallbackContext
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from api.google_maps import (
    Distance,
    get_location,
    get_photo,
    haversine
)

# Import the logger from the main module
logger = logging.getLogger(__name__)


def text_response(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = update.message.text
    logger.info(f"= Got on chat #{chat_id}: {text!r}")
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

    if msg_type == 0:
        # Receiving a single (non-live) location
        logger.info(
            f"= Got Single (non-live) location {message['location']} on chat #{chat_id}"
        )
    elif msg_type == 1:
        # The user has stopped sharing its Live Location
        logger.info(f"= Live Location paused. Chat ID: #{chat_id}")
        context.bot.send_message(chat_id, f"{'-' * 5} Live Location Paused {'-' * 5}")

    elif msg_type == 2:
        # At this point the user started sharing its Live Location

        origin = (message["location"]["latitude"], message["location"]["longitude"])  # Current location

        # Creating a Distance object for the user that will mainly be used to do various distance calculations
        context.user_data["distance"] = Distance(origin, context.user_data["key_name"])
        logger.info(
            f"= Start of live period: Got location {message['location']} on chat #{chat_id}"
        )

        # Context.user_data['distance'].destination is the randomly generated location at the distance the user
        # Specified. It's a dictionary of which the 'result' key holds the information of the random place
        context.user_data['destination'] = get_location(*context.user_data['distance'].destination)

        # Keeping the location of our destination in user_data
        context.user_data['destination_location'] = context.user_data['destination']['result']['geometry']['location']

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
            context.bot.sendPhoto(chat_id=chat_id, photo=photo_url)
            logger.info(f"On chat #{chat_id} Sent a photo of {location_name}")

            # We should skip to the next result if no photo is available
        except IndexError:
            logger.info(f"For chat #{chat_id} there are no photos of {location_name}")
            return
        context.bot.send_message(chat_id,
                                 f"Looks familiar? 🧐\n\nYour mission: Observe the photo above and try to "
                                 f"get there without using a map 🚫🗺")
    elif msg_type == 3:
        # We get an updated location from the user sharing his live location

        context.user_data["current_location"] = {'latitude': message["location"]["latitude"],
                                                 'longitude': message["location"]["longitude"]}
        logger.info(
            f'= Live Location received: {message["location"]}. Chat ID: #{chat_id}'
        )

        current_distance = int((haversine(context.user_data['destination_location']['lat'],
                                          context.user_data['destination_location']['lng'],
                                          context.user_data['current_location']['latitude'],
                                          context.user_data['current_location']['longitude'])) * 1000)

        # Updating the user with his distance from location
        logger.info(f"Your current distance from {context.user_data['destination']['result']['name']}"
                    f"is {current_distance} meters")
