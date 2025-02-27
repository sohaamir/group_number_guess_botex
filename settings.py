from os import environ

SESSION_CONFIGS = [
    dict(
        name='group_number_guess',
        display_name="Group Number Guessing Game",
        app_sequence=['instructions', 'game'],
        num_demo_participants=3,
        num_rounds=3,  # Number of rounds to play
        group_size=3,  # Players per group
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.00,
    participation_fee=0.00,
    doc="",
    group_by_arrival_time_timeout=3600,  # 1 hour in seconds
)

PARTICIPANT_FIELDS = ['name', 'total_score']
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'
# ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '{{ secret_key }}'
INSTALLED_APPS = ['otree']

# Rooms configuration for testing
ROOMS = [
    dict(
        name='number_guess_room',
        display_name='Number Guessing Game Room',
    ),
]