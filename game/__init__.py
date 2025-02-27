

from otree.api import *
import random
import time

class Constants(BaseConstants):
    name_in_url = 'game'
    players_per_group = 3  # Default value, will be overridden by session config
    num_rounds = 2  # Default value, will be overridden by session config
    guess_time_seconds = 10  # Time limit for guessing
    result_time_seconds = 10  # Time to display results before next round

class Subsession(BaseSubsession):
    def creating_session(self):
        # Set the actual number of rounds and players per group from session config
        if 'num_rounds' in self.session.config:
            self.session.vars['num_rounds'] = self.session.config['num_rounds']
        if 'group_size' in self.session.config:
            self.session.vars['group_size'] = self.session.config['group_size']
        
        # Create groups randomly in round 1
        if self.round_number == 1:
            self.group_randomly()
        else:
            # Keep the groups the same across rounds
            self.group_like_round(1)
            
        # Generate a target number for each group in this round
        for group in self.get_groups():
            group.target_number = random.randint(0, 100)
            print(f"ROUND {self.round_number}, TARGET: {group.target_number}")

class Group(BaseGroup):
    target_number = models.IntegerField()  # No initial value
    all_players_ready = models.BooleanField(initial=False)

class Player(BasePlayer):
    guess = models.IntegerField(
        min=0, 
        max=100, 
        label="Enter your guess (0-100):"
    )
    
    score = models.IntegerField(initial=0)  # Score for the current round
    total_score = models.IntegerField(initial=0)  # Cumulative score across all rounds
    rank = models.IntegerField(initial=0)  # Rank within the group for this round
    final_rank = models.IntegerField(initial=0)  # Final rank after all rounds
    
    # Store player's name
    name = models.StringField(initial="")
    
    # Add this field to track if player has submitted a guess
    has_submitted = models.BooleanField(initial=False)
    
    def guess_error_message(self, value):
        if value < 0 or value > 100:
            return 'Your guess must be between 0 and 100.'
    
    def calculate_score(self):
        # Use field_maybe_none to safely access potentially null target_number
        target = self.group.field_maybe_none('target_number')
        
        # If target is None, generate a random one
        if target is None:
            target = random.randint(0, 100)
            self.group.target_number = target
            print(f"ROUND {self.round_number}, TARGET: {target} (generated)")
        
        # Calculate score
        self.score = abs(self.guess - target)
        print(f"  Score for this round: {self.score}")
        
        # Update total score
        if self.round_number == 1:
            self.total_score = self.score
        else:
            prev_player = self.in_round(self.round_number - 1)
            self.total_score = prev_player.total_score + self.score
        
        # Always set name from participant if available
        if hasattr(self.participant, 'name') and self.participant.name:
            self.name = self.participant.name
        
        return self.score
        
    def calculate_rankings_for_group(self):
        """Calculate rankings for all players in the group"""
        players = self.group.get_players()
        
        # Sort players by score (lower is better)
        sorted_players = sorted(players, key=lambda p: p.score)
        
        # Assign ranks
        print(f"\nROUND {self.round_number} SCORES:")
        for i, p in enumerate(sorted_players):
            p.rank = i + 1
            print(f"  {p.name}: {p.score} (rank {p.rank})")
        
        # If this is the final round, calculate final rankings
        if self.round_number == self.session.config.get('num_rounds', Constants.num_rounds):
            # Sort by total score across all rounds (lower is better)
            sorted_players = sorted(players, key=lambda p: p.total_score)
            
            # Assign final ranks
            print(f"\nFINAL RANKINGS:")
            for i, p in enumerate(sorted_players):
                p.final_rank = i + 1
                print(f"  Position {p.final_rank}: {p.name} - {p.total_score} points")

    def get_results_data(self):
        """Get formatted results data for the current round"""
        players = self.group.get_players()
        players_data = []
        
        for p in players:
            # Make sure name is never None
            player_name = p.name if p.name else f"Player {p.id_in_group}"
            
            players_data.append({
                'id': p.id_in_group,
                'name': player_name,
                'guess': p.guess,
                'score': p.score,
                'rank': p.rank,
            })
        
        # Sort by rank
        players_data = sorted(players_data, key=lambda p: p['rank'])
        
        return {
            'target_number': self.group.target_number,
            'players_data': players_data,
            'round_number': self.round_number,
            'total_rounds': self.session.config.get('num_rounds', Constants.num_rounds),
        }

# PAGES
class WaitForGroup(WaitPage):
    template_name = 'game/WaitForGroup.html'
    group_by_arrival_time = True
    
    def is_displayed(self):
        return self.round_number == 1
    
    def vars_for_template(self):
        session = self.session
        current_time = time.time()
        
        # Record this player's refresh time
        self.participant.vars['last_refresh_time'] = current_time
        
        # Count only participants who have refreshed in the last 7 seconds
        waiting_participants = len([
            p for p in session.get_participants()
            if (p._current_page_name == 'WaitForGroup' and 
                p._current_app_name == 'game' and
                current_time - p.vars.get('last_refresh_time', 0) < 7)
        ])
        
        group_size = self.session.config.get('group_size', Constants.players_per_group)
        players_needed = max(0, group_size - waiting_participants % group_size)
        if players_needed == group_size:
            players_needed = 0
            
        return {
            'waiting_count': waiting_participants,
            'group_size': group_size,
            'players_needed': players_needed
        }

class Game(Page):
    form_model = 'player'
    form_fields = ['guess']
    timeout_seconds = Constants.guess_time_seconds
    
    def live_method(player, data):
        # Handle live updates during the game
        if 'submitted_guess' in data:
            # Store the guess
            player.guess = data['submitted_guess']
            # Mark player as having submitted
            player.has_submitted = True
            # No save() needed in oTree - it's automatic
            
            print(f"Player {player.id_in_group} submitted guess: {player.guess}")
            
            # Calculate score right away
            player.calculate_score()
            
            # Check if all players have submitted
            all_submitted = all(p.has_submitted for p in player.group.get_players())
            
            if all_submitted:
                # Calculate rankings for the group
                player.calculate_rankings_for_group()
                
                # Get result data for all players
                results_data = player.get_results_data()
                
                # Return results to all players
                return {0: {'phase': 'results', 'results': results_data}}
            else:
                # Confirm submission to the submitting player only
                return {player.id_in_group: {'phase': 'waiting', 'guess': player.guess}}
    
    def before_next_page(player, timeout_happened):
        # Make sure name is set from participant
        if hasattr(player.participant, 'name') and player.participant.name:
            player.name = player.participant.name
        
        # Only override guess if player truly didn't submit anything
        if (timeout_happened and not player.has_submitted):
            print(f"Player {player.id_in_group} ({player.name}): No submission, defaulting to 100")
            player.guess = 100
            player.has_submitted = True  # Mark as submitted now
            
            # Calculate the score
            player.calculate_score()
        
        # If score hasn't been calculated yet, do it now
        if player.score == 0 and player.guess is not None:
            print(f"Player {player.id_in_group} ({player.name}): Calculating score for guess {player.guess}")
            player.calculate_score()
        
        # If rankings haven't been calculated yet, do it now
        if player.rank == 0:
            player.calculate_rankings_for_group()
    
    def vars_for_template(self):
        return {
            'guess_time_seconds': Constants.guess_time_seconds,
            'result_time_seconds': Constants.result_time_seconds,
            'round_number': self.round_number,
            'total_rounds': self.session.config.get('num_rounds', Constants.num_rounds),
        }

class Results(Page):
    def is_displayed(self):
        # Only display on the final round
        return self.round_number == self.session.config.get('num_rounds', Constants.num_rounds)
    
    def vars_for_template(self):
        players = self.group.get_players()
        players_data = []
        
        # Build players data from the database
        for p in players:
            players_data.append({
                'name': p.name,
                'total_score': p.total_score,
                'final_rank': p.final_rank,
            })
        
        # Sort by final rank
        players_data = sorted(players_data, key=lambda p: p['final_rank'])
        
        # Debug to verify consistent scores
        print("\nFINAL SCORE TABLE:")
        for p in players_data:
            print(f"  {p['name']}: {p['total_score']} (rank {p['final_rank']})")
        
        return {
            'players_data': players_data,
            'player_total_score': self.total_score,
            'player_final_rank': self.final_rank,
            'player_name': self.name
        }

page_sequence = [
    WaitForGroup,
    Game,
    Results,
]