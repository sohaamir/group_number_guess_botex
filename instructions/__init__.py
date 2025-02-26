from otree.api import *

class Constants(BaseConstants):
    name_in_url = 'instructions'
    players_per_group = None
    num_rounds = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    name = models.StringField(label="Please enter your name:")

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
    pass

page_sequence = [Name, Instructions]