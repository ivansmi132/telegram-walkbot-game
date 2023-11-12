from uuid import uuid4
import logging

# Import the logger from the main module
logger = logging.getLogger(__name__)

# Database functions are subject to change


def put_db(update, context, user_id, key, value):
    # Store value
    context.user_data[key] = value
    # Send the key to the user
    update.message.reply_text(key)
    # Logging the action
    logger.info(f"database> key={key} : value={value} <has been stored or updated")


def get_db(update, context):
    """Usage: /get uuid"""
    # Separate ID from command (args[0] is where the user_id is stored)
    key = context.args[0]
    # Load value and send it to the user
    value = context.user_data.get(key, "Not found")
    # Logging the action
    logger.info(f"database> key={key} : value={value} <has been fetched")
    return value
