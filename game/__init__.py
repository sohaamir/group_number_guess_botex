author = 'Aamir Sohail'

doc = """
A simple oTree experiment where players compete in estimating a randomly generated number between 0-100 across multiple rounds.
"""

from otree.api import *
import random
import time

# Constants - varaibles that stay the same throughout the experiment
class C(BaseConstants):
    NAME_IN_URL = 'game'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 3
    GUESS_TIME_SECONDS = 10

# Subsession class - we don't have any variables, but we define a method to create groups 
# i.e., Subsession - for all groups in the session
class Subsession(BaseSubsession):
    def creating_session(self):

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

# Group - for all players in a group
# We simply have one variable here - the target number which is the same for all members of the group
class Group(BaseGroup):
    target_number = models.IntegerField()  # No initial value

# Player - a single member of the group
# We have several variables here: guess (which we assign a dictionary reflecting the properties of the guess)
# score, total_score, rank, final_rank, computer_guess, name, has_submitted
class Player(BasePlayer):
    guess = models.IntegerField(
        min=0, 
        max=100, 
        label="Enter your guess (0-100):",
        blank=True,
        null=True
    )
    
    score = models.IntegerField(initial=0)  # Score for the current round
    total_score = models.IntegerField(initial=0)  # Cumulative score across all rounds
    rank = models.IntegerField(initial=0)  # Rank within the group for this round
    final_rank = models.IntegerField(initial=0)  # Final rank after all rounds
    computer_guess = models.BooleanField(initial=False)  # Track if guess was made by computer
    
    # Store player's name
    name = models.StringField(initial="")
    
    # Add this field to track if player has submitted a guess
    has_submitted = models.BooleanField(initial=False)
    
    # Show an error message if the guess is out of range
    def guess_error_message(self, value):
        if value is not None and (value < 0 or value > 100):
            return 'Your guess must be between 0 and 100.'
    
    # Method to calculate the score for current rounds and across rounds
    def calculate_score(self):
        # Use field_maybe_none to safely access potentially null target number
        target = self.group.field_maybe_none('target_number')
        
        # If target is None, generate a random one
        if target is None:
            target = random.randint(0, 100)
            self.group.target_number = target
            print(f"ROUND {self.round_number}, TARGET: {target} (generated)")
        
        # Calculate score - safely check guess using field_maybe_none
        guess = self.field_maybe_none('guess')
        if guess is not None:
            self.score = abs(guess - target)
        else:
            # If no guess was made, explicitly set to 100
            self.score = 100
            
        print(f"  Score for this round: {self.score}")
        
        # Update total score by explicitly summing all rounds
        self.total_score = sum(self.in_round(r).score for r in range(1, self.round_number + 1))
        
        # Always set name from participant if available
        if hasattr(self.participant, 'name') and self.participant.name:
            self.name = self.participant.name
        elif not self.name or self.name.strip() == "":
            self.name = f"Player {self.id_in_group}"
        
        # Ensure name consistency across rounds - copy name to all rounds
        if self.round_number > 1:
            prev_player = self.in_round(self.round_number - 1)
            if prev_player.name and prev_player.name.strip() != "":
                self.name = prev_player.name
        
        return self.score
    
    # Method to catch any missing scores just in case
    def ensure_all_rounds_scored(self):
        """Ensure all rounds up to the current round have scores properly set"""
        for r in range(1, self.round_number + 1):
            round_player = self.in_round(r)

            if not round_player.has_submitted:
                # If player didn't submit in this round, mark as timeout
                round_player.has_submitted = True
                round_player.computer_guess = True
                round_player.guess = None
                round_player.score = 100
                print(f"Fixing missing score for {round_player.name} in round {r}: set to 100")

            elif round_player.has_submitted and round_player.score == 0:
                # For safety, check the guess value using field_maybe_none
                guess = round_player.field_maybe_none('guess')

                if guess is None:
                    # If player is marked as submitted but score is 0 and guess is None (timeout)
                    round_player.score = 100
                    round_player.computer_guess = True
                    print(f"Fixing incorrect score for {round_player.name} in round {r}: set to 100")
                
        # Recalculate total score
        self.total_score = sum(self.in_round(r).score for r in range(1, self.round_number + 1))
        
    # Method to calculate the rankings for all players in the group
    # We also ensure that all players have valid names and scores
    def calculate_rankings_for_group(self):
        """Calculate rankings for all players in the group"""
        players = self.group.get_players()
        
        # Make sure all players have valid names and scores
        for p in players:
            # Ensure name consistency
            if self.round_number > 1:
                prev_player = p.in_round(1)
                if prev_player.name and prev_player.name.strip() != "":
                    p.name = prev_player.name
            
            if not p.name or p.name.strip() == "":
                p.name = f"Player {p.id_in_group}"
            
            # Ensure all rounds are properly scored for this player
            p.ensure_all_rounds_scored()
            
            # Ensure all players have their scores calculated for the current round
            guess = p.field_maybe_none('guess')
            if p.has_submitted and p.score == 0 and guess is not None:
                p.calculate_score()
            elif not p.has_submitted:
                # Handle any players who somehow haven't been marked as submitted
                p.has_submitted = True  # Mark as submitted
                p.computer_guess = True  # Mark as a computer guess
                p.guess = None  # Leave guess as None for timed-out players
                p.score = 100  # Directly set score to 100
                
                print(f"Player {p.id_in_group} ({p.name}): No submission, setting score to 100")
            
            # Explicitly recalculate total score for all players by summing all rounds
            p.total_score = sum(p.in_round(r).score for r in range(1, p.round_number + 1))
            print(f"Updated total score for {p.name}: {p.total_score}")
        
        # Sort players by score (lower is better)
        sorted_players = sorted(players, key=lambda p: p.score)
        
        # Assign ranks
        print(f"\nROUND {self.round_number} SCORES:")
        for i, p in enumerate(sorted_players):
            p.rank = i + 1
            print(f"  {p.name}: {p.score} (rank {p.rank})")
        
        # If this is the final round, calculate final rankings
        if self.round_number == C.NUM_ROUNDS:
            # Ensure all rounds for all players are properly scored
            for p in players:
                for r in range(1, C.NUM_ROUNDS + 1):
                    round_player = p.in_round(r)
                    if not round_player.has_submitted:
                        round_player.has_submitted = True
                        round_player.computer_guess = True
                        round_player.guess = None
                        round_player.score = 100
                        print(f"Final fixing for {round_player.name} in round {r}: set to 100")
                    elif round_player.has_submitted and round_player.score == 0:
                        # Check guess value safely
                        guess = round_player.field_maybe_none('guess')
                        if guess is None:
                            round_player.score = 100
                            round_player.computer_guess = True
                            print(f"Final fixing score for {round_player.name} in round {r}: set to 100")
                
                # Calculate total score across all rounds
                p.total_score = sum(p.in_round(r).score for r in range(1, C.NUM_ROUNDS + 1))
                print(f"Final calculation - {p.name}: Total score {p.total_score}")
            
            # Sort by total score across all rounds (lower is better)
            sorted_by_total = sorted(players, key=lambda p: p.total_score)
            
            # Assign final ranks
            print(f"\nFINAL RANKINGS:")
            for i, p in enumerate(sorted_by_total):
                p.final_rank = i + 1
                print(f"  Position {p.final_rank}: {p.name} - {p.total_score} points")

    # Method to get formatted results data for the current round
    def get_results_data(self):
        """Get formatted results data for the current round"""
        players = self.group.get_players()
        players_data = []
        
        for p in players:
            # Make sure name is never None or empty
            player_name = p.name if p.name and p.name.strip() != "" else f"Player {p.id_in_group}"
            
            players_data.append({
                'id': p.id_in_group,
                'name': player_name,
                'guess': p.field_maybe_none('guess'),  # Safely access guess
                'score': p.score,
                'rank': p.rank,
            })
        
        # Sort by rank
        players_data = sorted(players_data, key=lambda p: p['rank'])
        
        # Return data which 
        return {
            'target_number': self.group.target_number,
            'players_data': players_data,
            'round_number': self.round_number,
            'total_rounds': C.NUM_ROUNDS,
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
        
        # Record the player's refresh time
        self.participant.vars['last_refresh_time'] = current_time
        
        # Count only participants who have refreshed in the last 7 seconds
        # Why 7? https://www.youtube.com/watch?v=T5a2OQuIZn0
        waiting_participants = len([
            p for p in session.get_participants()
            if (p._current_page_name == 'WaitForGroup' and 
                p._current_app_name == 'game' and
                current_time - p.vars.get('last_refresh_time', 0) < 7)
        ])
        
        group_size = C.PLAYERS_PER_GROUP
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
    timeout_seconds = C.GUESS_TIME_SECONDS
    
    def live_method(player, data):
        # Handle live updates during the game
        if 'submitted_guess' in data:
            # Store the guess
            player.guess = data['submitted_guess']

            # Mark player as having submitted
            player.has_submitted = True
            
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
        # Make sure name is set correctly and consistently
        if hasattr(player.participant, 'name') and player.participant.name:
            player.name = player.participant.name
        elif not player.name or player.name.strip() == "":
            player.name = f"Player {player.id_in_group}"
        
        # If this is not round 1, ensure name consistency with previous rounds
        if player.round_number > 1:
            prev_player = player.in_round(player.round_number - 1)
            if prev_player.name and prev_player.name.strip() != "":
                player.name = prev_player.name
        
        # Handle timeout - set score to 100 but leave guess as None
        if (timeout_happened and not player.has_submitted):
            player.has_submitted = True  # Mark as submitted
            player.computer_guess = True  # Mark as a computer guess
            player.guess = None  # Leave guess as None for timeout
            player.score = 100  # Directly set score to 100
            
            print(f"Player {player.id_in_group} ({player.name}): No submission, setting score to 100")
        
        # If score hasn't been calculated yet, do it now (for players who submitted guesses)
        # Use field_maybe_none to safely check the guess field
        elif player.has_submitted and player.score == 0:
            guess = player.field_maybe_none('guess')
            if guess is not None:
                print(f"Player {player.id_in_group} ({player.name}): Calculating score for guess {guess}")
                player.calculate_score()
            else:
                # This is a timeout case where the player has been marked as submitted but the score wasn't set properly
                player.score = 100
                player.computer_guess = True
                print(f"Player {player.id_in_group} ({player.name}): Fixing missed timeout score")
        
        # Ensure all previous rounds are properly scored
        player.ensure_all_rounds_scored()
        
        # Now calculate rankings after all players have their scores
        # Only do this calculation once per group per round
        if all(p.has_submitted for p in player.group.get_players()) and any(p.rank == 0 for p in player.group.get_players()):
            player.calculate_rankings_for_group()
    
    def vars_for_template(self):
        return {
            'GUESS_TIME_SECONDS': C.GUESS_TIME_SECONDS,
            'round_number': self.round_number,
            'total_rounds': C.NUM_ROUNDS,
        }

class Results(Page):
    def is_displayed(self):
        # Only display on the final round
        return self.round_number == C.NUM_ROUNDS
    
    def vars_for_template(self):
        players = self.group.get_players()
        
        # Force recalculation of final rankings
        # First, ensure all players in all rounds have proper scores
        for p in players:
            for r in range(1, C.NUM_ROUNDS + 1):
                round_player = p.in_round(r)
                # Ensure name consistency
                if r > 1:
                    prev_player = p.in_round(1)
                    if prev_player.name and prev_player.name.strip() != "":
                        round_player.name = prev_player.name
                
                if not round_player.name or round_player.name.strip() == "":
                    round_player.name = f"Player {round_player.id_in_group}"
                
                # Check if player has a valid score for this round
                if not round_player.has_submitted:
                    # Player never submitted in this round
                    round_player.has_submitted = True
                    round_player.computer_guess = True
                    round_player.guess = None
                    round_player.score = 100
                    print(f"Results fixing: {round_player.name} in round {r} never submitted. Set score to 100")
                elif round_player.has_submitted and round_player.score == 0:
                    # Check guess using field_maybe_none
                    guess = round_player.field_maybe_none('guess')
                    if guess is None:
                        # Player timed out but score wasn't set correctly
                        round_player.score = 100
                        round_player.computer_guess = True
                        print(f"Results fixing: {round_player.name} in round {r} timed out but score was 0. Set to 100")
            
            # Explicitly recalculate total score from all rounds
            round_scores = [p.in_round(r).score for r in range(1, C.NUM_ROUNDS + 1)]
            p.total_score = sum(round_scores)
            print(f"Results page - {p.name}: Round scores {round_scores}, Total: {p.total_score}")
        
        # Recalculate final rankings
        sorted_by_total = sorted(players, key=lambda p: p.total_score)
        for i, p in enumerate(sorted_by_total):
            p.final_rank = i + 1
            print(f"Final rank for {p.name}: {p.final_rank} with total score {p.total_score}")
        
        players_data = []
        
        # Build players data from the database
        for p in players:
            player_name = p.name if p.name and p.name.strip() != "" else f"Player {p.id_in_group}"
            players_data.append({
                'name': player_name,
                'total_score': p.total_score,
                'final_rank': p.final_rank,
            })
        
        # Sort by final rank
        players_data = sorted(players_data, key=lambda p: p['final_rank'])
        
        # Debug to verify consistent scores
        print("\nFINAL SCORE TABLE:")
        for p in players_data:
            print(f"  {p['name']}: {p['total_score']} (rank {p['final_rank']})")
        
        my_name = self.name if self.name and self.name.strip() != "" else f"Player {self.id_in_group}"
        
        return {
            'players_data': players_data,
            'player_total_score': self.total_score,
            'player_final_rank': self.final_rank,
            'player_name': my_name
        }

# If using humans (i.e., not LLM bots using botex), re-add the WaitForGroup page before the Game page
page_sequence = [
    Game,
    Results,
]