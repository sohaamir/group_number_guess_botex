# This script runs a botex experiment using the oTree server.

from dotenv import load_dotenv
from os import environ
import logging
import botex
import os

# Set logging level
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
if os.path.exists('.env'):
    load_dotenv()
    os.environ['OTREE_REST_KEY'] = environ.get('OTREE_REST_KEY', '')

# Will be created in the current directory if it does not exist
BOTEX_DB = "botex.sqlite3"

# Path to your oTree project folder if you want the code to start the server
OTREE_PROJECT_PATH = "."

# Change the oTree URL if you are using a remote server
OTREE_URL = "http://localhost:8000"

# Get REST key from environment
OTREE_REST_KEY = environ.get('OTREE_REST_KEY', '')

# Admin credentials
OTREE_ADMIN_USERNAME = 'admin'
OTREE_ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

# LLM model vars
LLM_MODEL = "gemini/gemini-1.5-flash"
LLM_API_KEY = environ.get('OTREE_GEMINI_API_KEY')

# Start the oTree server - if not using an already running server
otree_process = botex.start_otree_server(project_path=OTREE_PROJECT_PATH)

# Get the available session configurations from the oTree server
session_configs = botex.get_session_configs(
    otree_server_url=OTREE_URL,
    otree_rest_key=OTREE_REST_KEY
)

# Initialize a session
session = botex.init_otree_session(
    config_name='group_number_guess',  # Updated to your game name
    npart=3,  # Updated to match your PLAYERS_PER_GROUP in game/__init__.py
    otree_server_url=OTREE_URL,
    otree_rest_key=OTREE_REST_KEY,
    botex_db=BOTEX_DB
)

# Run the bots on the session
print(
    f"Starting bots. You can monitor their progress at "
    f"{OTREE_URL}/SessionMonitor/{session['session_id']}"
)
botex.run_bots_on_session(
    session_id=session['session_id'],
    botex_db=BOTEX_DB,
    model=LLM_MODEL,
    api_key=LLM_API_KEY,
    throttle=True
)

# Export oTree data
botex.export_otree_data(
    "group_number_guess_otree_wide.csv",
    server_url=OTREE_URL,
    admin_name=OTREE_ADMIN_USERNAME,
    admin_password=OTREE_ADMIN_PASSWORD
)
botex.normalize_otree_data(
    "group_number_guess_otree_wide.csv", 
    store_as_csv=True,
    exp_prefix="group_number_guess_otree"
)

# Export botex data
botex.export_participant_data(
    "group_number_guess_botex_participants.csv",
    botex_db=BOTEX_DB
)

try:
    botex.export_response_data(
        "group_number_guess_botex_responses.csv",
        botex_db=BOTEX_DB,
        session_id=session['session_id']
    )
except IndexError:
    print("No bot responses found. This may happen if bots didn't complete any form submissions.")

# Stop the oTree server
botex.stop_otree_server(otree_process)