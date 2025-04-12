from os import environ
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This is useful for local development
if os.path.exists('.env'):
    load_dotenv()
    os.environ['OTREE_REST_KEY'] = environ.get('OTREE_REST_KEY', '')

# SECURITY CONFIGURATION
# ---------------------
# Set to True for development, False for production
DEBUG = environ.get('OTREE_PRODUCTION') != '1'

# Secret key - used for cryptographic signing
# In production, this should be set as an environment variable
SECRET_KEY = environ.get('OTREE_SECRET_KEY', '{{ secret_key }}')

# Admin password - used to access the admin interface
# In production, this should be set as an environment variable
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

# Allowed hosts - domains that this app can serve - localhost and Heroku app site
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
     '.group-number-guess-270c0fad5a0f.herokuapp.com/',
]

# APPLICATION CONFIGURATION
# ------------------------
SESSION_CONFIGS = [
    dict(
        name='group_number_guess',
        display_name="Group Number Guessing Game",
        app_sequence=['instructions', 'game'],
        num_demo_participants=3,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.00,
    participation_fee=0.00,
    doc="",
    group_by_arrival_time_timeout=3600,
)

# Fields to persist between apps
PARTICIPANT_FIELDS = ['name', 'total_score']
SESSION_FIELDS = []

# Localization settings
LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

# Demo page configuration
DEMO_PAGE_INTRO_HTML = """ """

# oTree core settings
INSTALLED_APPS = ['otree']

# Authentication level - determines what pages users can access
# Options: DEMO, STUDY, INDIVIDUAL_DEMO (default: DEMO)
AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL', 'DEMO')

# Rooms configuration for testing
ROOMS = [
    dict(
        name='group_number_guess',
        display_name='Number Guessing Game Room',
    ),
]



################# botex settings #################

# Botex settings
