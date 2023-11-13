from enum import Enum
import logging

# Import the logger from the main module
logger = logging.getLogger(__name__)


class StateStages(Enum):
    UNDEFINED = -1
    BEFORE_START = 0  # /cancel ----> 0, /start ----> 1
    ASKING_DISTANCE = 1  # selected distance ----> 2, /cancel ----> 0, /start ----> 1
    ASKING_LIVE_LOCATION = 2  # live sent ----> 3, normal location sent ----> 2, /cancel ----> 0, /start ----> 1
    LOCATION_SELECTION_LOOP = 3  # if another ----> 3, if accept ----> 5, /cancel ----> 0, /start ----> 1
    GAME_START = 4  # instant ----> 5
    PLAYING_LOOP = 5  # while not done ----> 5, arrived ----> 6, /cancel ----> 0, /start ----> 1
    WIN_SCREEN = 6  # instant ----> 7,
    REPLAY_SCREEN = 7  # (yes, /start) ----> 1, (no, /cancel) ----> 0,
    PAUSED = 8  # live sent ---->


def set_user_state(user_data, state):
    user_data['state'] = state
    logger.info(
        f">>>>>>>>> Just Entered State: {get_user_state(user_data)} in state machine <<<<<<<<<")


def get_user_state(user_data):
    try:
        curr_state = user_data['state']
        return curr_state
    except KeyError:
        return StateStages.UNDEFINED
