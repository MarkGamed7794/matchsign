# -- DATA REQUESTS -- #

import yaml, dotenv

with open("configuration/constants.yaml", 'r') as file:
    constants = yaml.safe_load(file)
with open("configuration/request_params.yaml", 'r') as file:
    request_params = yaml.safe_load(file)

DEBUG_MODE = False

TEAM_NUMBER = constants["team_number"]

DISABLE_REQUESTS = constants["requests"]["disable_requests"]
REQUEST_SOURCE = constants["requests"]["request_source"]
TBA_CACHE_FILEPATH = constants["requests"]["tba_cache_filepath"]
REQUEST_TIMEOUT = constants["requests"]["request_timeout"]

USE_CACHED_DATA = constants["requests"]["response_cache"]["use_cache"]
SAVE_RESPONSE = constants["requests"]["response_cache"]["save_response"]

REQUEST_RETRY_LIMIT = constants["requests"]["request_parameters"]["retry_limit"]
SHOW_RESPONSE_BODY = constants["requests"]["request_parameters"]["print_response_body"]

env_config = dotenv.dotenv_values()
FRC_AUTH = env_config["FRC_AUTH"] if "FRC_AUTH" in env_config else ""
TBA_AUTH = env_config["TBA_AUTH"] if "TBA_AUTH" in env_config else ""
NEXUS_AUTH = env_config["NEXUS_AUTH"] if "NEXUS_AUTH" in env_config else ""

REQUEST_PARAMS = { # The parameters for each request.
    "season": request_params["frc"]["season"],
    
    "team_number_frc": request_params["frc"]["team_number"],
    "event_code_frc": request_params["frc"]["event_code"],
    "tournament_level": request_params["frc"]["tournament_level"],
    
    "team_key_tba": request_params["tba"]["team_key"],
    "event_key_tba": request_params["tba"]["event_key"],

    "event_key_nexus": request_params["nexus"]["event_key"]
}


# -- DISPLAY AND INPUT -- #
PYGAME_MODE = constants["output"]["pygame_mode"]

LED_WIDTH = constants["output"]["led"]["cols"]
LED_HEIGHT = constants["output"]["led"]["rows"]
LED_CHAIN_LENGTH = constants["output"]["led"]["chain_length"]
LED_CHAIN_COUNT = constants["output"]["led"]["chain_count"]

RPI_KEYPAD_ROWS = constants["input"]["rpi_keypad_rows"]
RPI_KEYPAD_COLS = constants["input"]["rpi_keypad_cols"]

BUTTON_SELECT = constants["keymap"]["button_select"]
BUTTON_LEFT   = constants["keymap"]["button_left"]
BUTTON_RIGHT  = constants["keymap"]["button_right"]
BUTTON_UP     = constants["keymap"]["button_up"]
BUTTON_DOWN   = constants["keymap"]["button_down"]