# poetry added imports
from telegram import Update
from bot_settings import BOT_TOKEN
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    PicklePersistence,
    CallbackQueryHandler,
)

# Default libraries
import logging
import os

# Our modules import
import api.google_maps as gm
import handlers.keyboard_handler as kb
import handlers.database_handler as db
import handlers.command_handler as ch
import handlers.message_handler as mh

# Configure the logger
logging.basicConfig(
    format="[%(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s",
    level=logging.INFO,
)

# Create a logger instance
logger = logging.getLogger(__name__)


def main():
    # Get bot API key
    bot_key = BOT_TOKEN

    # Persistence file ( This is how the user data can be saved even after turning off our bot )
    my_persistence = PicklePersistence(filename="saved_memory")

    # Updater
    my_bot = Updater(token=bot_key, persistence=my_persistence, use_context=True)

    # Dispatcher
    dp = my_bot.dispatcher

    # Commands handler
    # dp.add_handler(CommandHandler('command', callback))
    dp.add_handler(CommandHandler("start", ch.start))
    dp.add_handler(CommandHandler("location", kb.location_keyboard_button))

    # Messages handler
    # dp.add_handler(MessageHandler(Filters.TYPE, callback))
    dp.add_handler(MessageHandler(Filters.text, mh.text_response))
    dp.add_handler(MessageHandler(Filters.voice, mh.voice_response))
    dp.add_handler(MessageHandler(Filters.location, mh.live_location_receiver))

    # Buttons
    dp.add_handler(CallbackQueryHandler(kb.button))

    # Google Maps location (this is just here so you guys can see the data
    # pprint(gm.get_location())

    logger.info("* Start polling...")
    my_bot.start_polling()  # Starts polling in a background thread.
    my_bot.idle()  # Wait until Ctrl+C is pressed
    logger.info("* Bye!")


# Run this if we are executing this file directly
if __name__ == "__main__":
    main()
