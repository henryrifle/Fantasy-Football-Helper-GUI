#Fanasty Football Draft Helper
import csv
from typing import List, Dict
import os
import tkinter as tk
from tkinter import filedialog, messagebox

class Player:
    def __init__(self, name, pos, team='', bye='', avg_rank=999):
        self.name = name
        self.pos = pos
        self.team = team
        self.bye = bye
        self.avg_rank = avg_rank

    def __str__(self):
        return f"{self.name} ({self.pos})"

class DraftHelper:
    def __init__(self, total_teams, your_position, total_rounds=15, roster_limits=None, lineup_settings=None):
        self.total_teams = total_teams
        self.your_position = your_position
        self.total_rounds = total_rounds
        
        # Use provided lineup settings or defaults
        self.lineup_settings = lineup_settings or {
            'QB': 1,
            'RB': 2,
            'WR': 2,
            'TE': 1,
            'K': 1,
            'DST': 1,
            'FLEX': 1
        }
        
        # Use provided roster limits or calculate from lineup settings
        self.roster_limits = roster_limits or {
            'QB': max(2, self.lineup_settings['QB']),
            'RB': max(6, self.lineup_settings['RB'] + self.lineup_settings.get('FLEX', 0)),
            'WR': max(6, self.lineup_settings['WR'] + self.lineup_settings.get('FLEX', 0)),
            'TE': max(2, self.lineup_settings['TE']),
            'K': max(1, self.lineup_settings['K']),
            'DST': max(1, self.lineup_settings['DST'])
        }
        
        # Initialize basic structures
        self.drafted_players = {i: [] for i in range(1, total_teams + 1)}
        self.team_names = {i: f"Team {i}" for i in range(1, total_teams + 1)}
        self.use_team_names = False
        self.available_players = []
        
        # Load players
        success = self.load_players()
        if not success:
            raise Exception("Failed to load player rankings.")

    def load_players(self):
        """Load player rankings from CSV file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rankings_path = os.path.join(current_dir, 'rankings.csv')
            
            print(f"Looking for rankings file at: {rankings_path}")
            
            if not os.path.exists(rankings_path):
                messagebox.showerror("Error", f"Rankings file not found at: {rankings_path}")
                return False
            
            with open(rankings_path, 'r', encoding='utf-8') as file:
                content = file.read().replace('"', '').strip('\ufeff')
                lines = content.split('\n')
                reader = csv.DictReader(lines)
                
                for row in reader:
                    try:
                        # Extract base position from POS field (e.g., 'RB1' -> 'RB')
                        full_pos = row.get('POS', '')
                        base_pos = ''.join(c for c in full_pos if not c.isdigit())
                        
                        player = Player(
                            name=row['Player'],
                            pos=base_pos,  # Use the cleaned position
                            team=row.get('Team', ''),
                            bye=row.get('Bye', ''),
                            avg_rank=float(row.get('Rank', 999))  # Use Rank instead of AVG
                        )
                        self.available_players.append(player)
                    except (KeyError, ValueError) as e:
                        print(f"Error processing row: {row}")
                        print(f"Error details: {str(e)}")
                        continue
                
                if not self.available_players:
                    messagebox.showerror("Error", "No valid players found in rankings file")
                    return False
                
                # Sort players by rank
                self.available_players.sort(key=lambda x: x.avg_rank)
                return True
                
        except Exception as e:
            messagebox.showerror("Error", f"Error loading rankings: {str(e)}")
            return False

    def get_current_drafter(self, pick_number):
        """Calculate which team is currently drafting based on the pick number"""
        round_number = (pick_number - 1) // self.total_teams + 1
        pick_in_round = (pick_number - 1) % self.total_teams + 1
        
        # If it's an even round, reverse the pick order (snake draft)
        if round_number % 2 == 0:
            pick_in_round = self.total_teams - pick_in_round + 1
            
        return pick_in_round

    def get_next_pick_number(self, current_pick):
        """Calculate when your next pick will be"""
        current_round = (current_pick - 1) // self.total_teams + 1
        next_round = current_round + 1
        
        if next_round % 2 == 1:  # Odd round
            next_pick = (next_round - 1) * self.total_teams + self.your_position
        else:  # Even round (snake)
            next_pick = next_round * self.total_teams - self.your_position + 1
            
        return next_pick

    def find_player(self, search_term):
        """Find a player by partial name match"""
        search_term = search_term.lower().strip()
        matching_players = []
        
        for player in self.available_players:
            # Split player name into parts and convert to lower case
            name_parts = player.name.lower().split()
            
            # Check if search term matches:
            # 1. Any part of the name exactly
            # 2. Start of any name part
            # 3. Full name contains the search term
            if (search_term in name_parts or  # Exact match with any part
                any(part.startswith(search_term) for part in name_parts) or  # Starts with search term
                search_term in player.name.lower()):  # Part of full name
                matching_players.append(player)
        
        return matching_players

    def draft_player(self, player_name, team_number):
        """Mark a player as drafted by a specific team"""
        matching_players = self.find_player(player_name)
        
        if not matching_players:
            return False, f"No players found matching '{player_name}'"
        elif len(matching_players) > 1:
            return False, matching_players
        else:
            player = matching_players[0]
            self.drafted_players[team_number].append(player)
            self.available_players.remove(player)
            return True, player

    def get_best_available(self, position=None, top_n=None):  # Made top_n optional
        available = []
        
        for player in self.available_players:
            # Skip if player is already drafted
            if any(p.name == player.name for team in self.drafted_players.values() for p in team):
                continue
                
            # Add player if no position filter or matches position
            if position is None or player.pos == position:
                available.append(player)
        
        # Sort by average rank
        available.sort(key=lambda x: x.avg_rank)
        
        # Return all players if top_n is None, otherwise return top_n players
        return available[:top_n] if top_n is not None else available

    def show_draft_board(self):
        """Display the current draft board"""
        print("\nDraft Board:")
        total_picks = len(sum(self.drafted_players.values(), []))
        total_rounds = (total_picks // self.total_teams) + 1
        
        for round_num in range(1, total_rounds + 1):
            print(f"\nRound {round_num}:")
            for pick_num in range(1, self.total_teams + 1):
                # Calculate the actual team number based on snake draft
                if round_num % 2 == 1:  # Odd rounds (1, 3, 5, etc.)
                    team_num = pick_num
                else:  # Even rounds (2, 4, 6, etc.)
                    team_num = self.total_teams - pick_num + 1
                
                # Calculate the index in the team's draft list
                pick_index = round_num - 1
                team_picks = self.drafted_players[team_num]
                
                if pick_index < len(team_picks):
                    player = team_picks[pick_index]
                    print(f"Pick {(round_num-1)*self.total_teams + pick_num}: Team {team_num} - {player.name} ({player.pos})")
                else:
                    print(f"Pick {(round_num-1)*self.total_teams + pick_num}: Team {team_num} - --")

    def get_team_needs(self, team_number):
        """Analyze what positions a team needs most and show current roster"""
        roster = self.drafted_players.get(team_number, [])
        needs = []
        
        # Count current positions
        pos_count = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
        for player in roster:
            pos_count[player.pos] += 1
        
        # Define position requirements
        requirements = {
            'QB': (1, 2),    # (min, max) desired
            'RB': (2, 4),
            'WR': (2, 4),
            'TE': (1, 2),
            'K': (1, 1),     # Only need 1 kicker
            'DST': (1, 1)    # Only need 1 defense
        }
        
        # Determine needs
        for pos, (min_req, max_req) in requirements.items():
            current = pos_count[pos]
            if current < min_req:
                priority = "High"
            elif current < max_req:
                priority = "Medium"
            else:
                priority = "Low"
                
            # Special handling for K and DST
            if pos in ['K', 'DST'] and current >= 1:
                continue  # Skip if already have one
                
            needs.append((pos, priority))
        
        # Sort needs by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        needs.sort(key=lambda x: priority_order[x[1]])
        
        # Format roster for display
        roster_display = []
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            pos_players = [p for p in roster if p.pos == pos]
            if pos_players:
                roster_display.append(f"{pos}: {', '.join(p.name for p in pos_players)}")
            else:
                roster_display.append(f"{pos}: None")
        
        return needs, roster_display

    def suggest_draft_pick(self, team_number, current_round, needs):
        """Suggest draft picks based on team needs and draft position"""
        suggestions = []
        
        # Get available players
        available_players = []
        for p in self.available_players:
            if not any(p.name == drafted.name for drafted in sum(self.drafted_players.values(), [])):
                available_players.append(p)
        
        # Position priorities by round
        round_priorities = {
            (1, 3): ['RB', 'WR'],  # Early rounds: Focus on RB/WR
            (4, 6): ['QB', 'TE'],   # Middle rounds: Look for QB/TE
            (7, 12): ['RB', 'WR', 'QB', 'TE'],  # Late middle: Best available core positions
            (13, 15): ['K', 'DST']  # Last rounds: Kicker and Defense
        }
        
        # Get current priorities based on round
        current_priorities = []
        for (start, end), positions in round_priorities.items():
            if start <= current_round <= end:
                current_priorities = positions
                break
        
        # Score each available player
        scored_players = []
        for player in available_players:
            score = 0
            
            # Base score from ranking
            score += (1000 - player.avg_rank) / 100
            
            # Bonus for team needs
            for pos, priority in needs:
                if player.pos == pos:
                    if priority == "High":
                        score += 30
                    elif priority == "Medium":
                        score += 15
                    elif priority == "Low":
                        score += 5
            
            # Bonus for round-appropriate positions
            if player.pos in current_priorities:
                score += 20
            
            # Penalty for drafting K/DST too early
            if player.pos in ['K', 'DST'] and current_round < 13:
                score -= 50
            
            scored_players.append((player, score))
        
        # Sort by score and convert to suggestions with priority labels
        scored_players.sort(key=lambda x: x[1], reverse=True)
        for player, score in scored_players[:8]:  # Show top 8 suggestions
            if score > 80:
                priority = "High"
            elif score > 50:
                priority = "Medium"
            else:
                priority = "Low"
            suggestions.append((player, priority))
        
        return suggestions

    def search_player_stats(self, search_name):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'fantasy_merged_7_17.csv')
            
            with open(csv_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                all_players = list(csv_reader)
                
                search_terms = search_name.lower().split()
                matching_players = []
                
                for row in all_players:
                    player_name = row['Player'].lower()
                    name_parts = player_name.split()
                    
                    # Check if any search term is a substring of any name part
                    if any(any(search_term in part or part in search_term 
                              for part in name_parts)
                           for search_term in search_terms):
                        matching_players.append(row)
                
                # Group by player name to get all years
                player_years = {}
                for player in matching_players:
                    name = player['Player']
                    if name not in player_years:
                        player_years[name] = []
                    player_years[name].append(player)
                
                # Sort each player's years in descending order
                for name in player_years:
                    player_years[name].sort(key=lambda x: int(x['Year']), reverse=True)
                
                return player_years
                
        except FileNotFoundError as e:
            print(f"Error: Could not find file at {csv_path}")
            return None
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return None

    def get_team_identifier(self, team_number):
        """Get either team name or number based on settings"""
        if self.use_team_names and team_number in self.team_names:
            return self.team_names[team_number]
        return f"Team {team_number}"

    def set_team_name(self, team_number, team_name):
        """Set a team name for a given team number"""
        self.team_names[team_number] = team_name

    def toggle_team_display(self):
        """Toggle between team names and numbers"""
        self.use_team_names = not self.use_team_names

def main():
    # Get draft setup information
    total_teams = int(input("Enter the total number of teams in the draft (e.g., 12): "))
    your_position = int(input(f"Enter your draft position (1-{total_teams}): "))
    
    roster_needs = {
        "QB": 2,
        "RB": 4,
        "WR": 5,
        "TE": 2,
        "K": 1,
        "DST": 1
    }

    helper = DraftHelper(total_teams, your_position)
    current_pick = 1
    
    while True:
        print("\nFantasy Football Draft Helper")
        print(f"Current Pick: {current_pick}")
        drafting_team = helper.get_current_drafter(current_pick)
        print(f"Drafting Team: {drafting_team}")
        
        if drafting_team == your_position:
            print("IT'S YOUR PICK!")
            next_pick = helper.get_next_pick_number(current_pick)
            print(f"Your next pick will be: {next_pick}")
            
            # Show team needs when it's your pick
            print("\nTeam Needs:")
            needs, roster = helper.get_team_needs(your_position)
            for pos, priority in needs:
                print(f"{pos}: {priority}")
            print("\nCurrent Roster:")
            for line in roster:
                print(line)
        
        print("\n1. Get draft suggestions")
        print("2. Draft a player")
        print("3. Show draft board")
        print("4. Show best available")
        print("5. Show team needs")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            suggestions = helper.suggest_draft_pick(drafting_team, current_pick, needs)
            print("\nTop Suggested Picks:")
            for i, (player, priority) in enumerate(suggestions, 1):
                print(f"{i}. {player.name} ({player.pos}) - Avg Rank: {player.avg_rank} - Priority: {priority}")
                
        elif choice == "2":
            player_name = input("Enter the name of the player drafted: ")
            drafting_team = helper.get_current_drafter(current_pick)
            success, result = helper.draft_player(player_name, drafting_team)
            
            if success:
                print(f"\nSuccessfully drafted {result.name} ({result.pos}) to Team {drafting_team}")
                current_pick += 1
            else:
                if isinstance(result, list):
                    print("\nMultiple matching players found:")
                    for i, player in enumerate(result, 1):
                        print(f"{i}. {player.name} ({player.pos}) - Avg Rank: {player.avg_rank}")
                    
                    while True:
                        choice = input("\nEnter the number of the correct player (or press Enter to cancel): ")
                        if not choice:  # User pressed Enter to cancel
                            break
                        if choice.isdigit() and 1 <= int(choice) <= len(result):
                            player = result[int(choice)-1]
                            success, _ = helper.draft_player(player.name, drafting_team)
                            if success:
                                print(f"\nSuccessfully drafted {player.name} ({player.pos}) to Team {drafting_team}")
                                current_pick += 1
                            break
                        print("Invalid choice. Please try again.")
                else:
                    print(f"\nError: {result}")
        
        elif choice == "3":
            helper.show_draft_board()
        
        elif choice == "4":
            position = input("Enter position to filter (or press Enter for all): ").upper()
            players = helper.get_best_available(position if position else None, top_n=10)
            print("\nBest Available Players:")
            for i, player in enumerate(players, 1):
                print(f"{i}. {player.name} ({player.pos}) - Avg Rank: {player.avg_rank}")
        
        elif choice == "5":
            team = int(input("Enter team number to check needs: "))
            needs, roster = helper.get_team_needs(team)
            print(f"\nTeam {team} Needs:")
            for pos, priority in needs:
                print(f"{pos}: {priority}")
            print("\nCurrent Roster:")
            for line in roster:
                print(line)
        
        elif choice == "6":
            break

if __name__ == "__main__":
    main()