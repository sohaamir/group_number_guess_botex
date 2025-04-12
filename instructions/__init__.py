from otree.api import *
from game import C as GameC

class C(BaseConstants):
    NAME_IN_URL = 'instructions'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    name = models.StringField(label="Your name:")

# PAGES
class Name(Page):
    form_model = 'player'
    form_fields = ['name']
    
    def before_next_page(player, timeout_happened):
        if not player.name:
            player.name = f"Player {player.id_in_group}"
            
        # Store in participant vars for access across apps
        player.participant.name = player.name
        print(f"PLAYER NAME: {player.name}")

class Instructions(Page):
    def vars_for_template(self):
        return {
            'NUM_ROUNDS': GameC.NUM_ROUNDS,
            'PLAYERS_PER_GROUP': GameC.PLAYERS_PER_GROUP,
            'GUESS_TIME_SECONDS': GameC.GUESS_TIME_SECONDS
        }

page_sequence = [Name, Instructions]