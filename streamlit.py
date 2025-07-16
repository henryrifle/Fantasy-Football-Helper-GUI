# fantasy_fb_gui_streamlit.py
import streamlit as st
import csv
import os
import json
from pathlib import Path
import hashlib
import time
import pandas as pd

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
    def __init__(self, total_teams, your_position, total_rounds=15, roster_limits=None, lineup_settings=None, auto_draft=False):
        self.total_teams = total_teams
        self.your_position = your_position
        self.total_rounds = total_rounds
        self.auto_draft = auto_draft
        
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

    def load_players(self, ranking_type='expert'):
        """Load player rankings from CSV file"""
        try:
            # First load expert rankings to get player positions
            expert_rankings_path = os.path.join(os.getcwd(), 'data_used', 'rankings3.csv')
            player_positions = {}
            seen_players = set()  # Track seen players to avoid duplicates
            
            with open(expert_rankings_path, 'r', encoding='utf-8') as file:
                content = file.read().replace('"', '').strip('\ufeff')
                lines = content.split('\n')
                reader = csv.DictReader(lines)
                for row in reader:
                    full_pos = row.get('POS', '')
                    base_pos = ''.join(c for c in full_pos if not c.isdigit())
                    player_positions[row['Player'].lower()] = base_pos

            # Choose file based on ranking type
            if ranking_type == 'ml':
                # Load both flex.csv (RB/WR/TE) and flex2.csv (QB) for ML rankings
                flex_path = os.path.join(os.getcwd(), 'data_used', 'flex.csv')
                flex2_path = os.path.join(os.getcwd(), 'data_used', 'flex2.csv')
                
                self.available_players = []  # Reset available players
                
                # First process flex.csv for both QB rushing and other positions
                qb_rushing_points = {}  # Store QB rushing points
                if os.path.exists(flex_path):
                    with open(flex_path, 'r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            try:
                                player_name = row['Player']
                                if player_name.lower() in seen_players:
                                    continue
                                
                                player_pos = player_positions.get(player_name.lower())
                                if not player_pos:
                                    continue

                                try:
                                    points = float(row['Predicted_FP'])
                                except ValueError:
                                    continue

                                if player_pos == 'QB':  # Store QB rushing points for later
                                    qb_rushing_points[player_name] = points
                                    print(f"Found rushing points for QB {player_name}: {points}")
                                elif player_pos in ['RB', 'WR', 'TE']:  # Process other positions normally
                                    player = Player(
                                        name=player_name,
                                        pos=player_pos,
                                        team=row.get('Team', ''),
                                        bye=row.get('Bye', ''),
                                        avg_rank=points
                                    )
                                    self.available_players.append(player)
                                    seen_players.add(player_name.lower())
                                    
                            except (KeyError, ValueError) as e:
                                print(f"Error processing flex.csv row: {row}")
                                print(f"Error details: {str(e)}")
                                continue

                # Process flex2.csv (QB)
                if os.path.exists(flex2_path):
                    with open(flex2_path, 'r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        print("flex2.csv columns:", reader.fieldnames)
                        for row in reader:
                            try:
                                player_name = row['Player']
                                if player_name.lower() in seen_players:
                                    continue
                                
                                player_pos = 'QB'
                                
                                try:
                                    # Combine passing and rushing points
                                    pass_points = float(row['Predicted_FP'])
                                    rush_points = qb_rushing_points.get(player_name, 0)  # Get rushing points or 0 if none
                                    total_points = pass_points + rush_points
                                    print(f"Processing QB {player_name}: {pass_points} passing + {rush_points} rushing = {total_points} total")
                                    
                                except ValueError as e:
                                    print(f"Value error for {player_name}: {e}")
                                    continue
                                
                                player = Player(
                                    name=player_name,
                                    pos=player_pos,
                                    team=row.get('Team', ''),
                                    bye=row.get('Bye', ''),
                                    avg_rank=total_points
                                )
                                self.available_players.append(player)
                                seen_players.add(player_name.lower())
                                
                            except (KeyError, ValueError) as e:
                                print(f"Error processing flex2.csv row: {row}")
                                print(f"Error details: {str(e)}")
                                continue

                return True  # Return True if we successfully loaded ML rankings
                
            else:
                # Expert rankings processing (unchanged)
                filename = 'rankings3.csv'
                rankings_path = os.path.join(os.getcwd(), 'data_used', filename)
                
                if not os.path.exists(rankings_path):
                    print("Rankings file not found.")
                    return False
                
                self.available_players = []
                
                with open(rankings_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        try:
                            player_name = row['Player']
                            if player_name.lower() in seen_players:
                                continue
                            
                            full_pos = row.get('POS', '')
                            player_pos = ''.join(c for c in full_pos if not c.isdigit())
                            try:
                                rank_value = float(row.get('Rank', 999))
                            except ValueError:
                                rank_value = 999
                        
                            player = Player(
                                name=player_name,
                                pos=player_pos,
                                team=row.get('Team', ''),
                                bye=row.get('Bye', ''),
                                avg_rank=rank_value
                            )
                            self.available_players.append(player)
                            seen_players.add(player_name.lower())
                            
                        except (KeyError, ValueError) as e:
                            print(f"Error processing row: {row}")
                            print(f"Error details: {str(e)}")
                            continue

                return True
                
        except Exception as e:
            print(f"Error loading rankings: {str(e)}")
            return False

    def search_player_stats(self, search_name):
        """Search for player stats in the CSV files"""
        try:
            # Get paths to both CSV files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qb_path = os.path.join(current_dir, 'data_used/historical_seasons_pass.csv')
            skill_path = os.path.join(current_dir, 'data_used/historical_seasons_scrim.csv')
            
            # Read both files
            all_players = []
            for csv_path in [qb_path, skill_path]:
                with open(csv_path, mode='r', encoding='utf-8') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    all_players.extend(list(csv_reader))
            
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
            print(f"Error: Could not find file: {e}")
            return None
        except Exception as e:
            print(f"Error reading CSV files: {str(e)}")
            return None

    def get_current_drafter(self, pick_number):
        """Calculate which team is currently drafting based on the pick number"""
        round_number = (pick_number - 1) // self.total_teams + 1
        pick_in_round = (pick_number - 1) % self.total_teams + 1
        
        # If it's an even round, reverse the pick order (snake draft)
        if round_number % 2 == 0:
            pick_in_round = self.total_teams - pick_in_round + 1
            
        return pick_in_round

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

    def get_best_available(self, position=None, top_n=None):
        available = []
        
        for player in self.available_players:
            # Skip if player is already drafted
            if any(p.name == player.name for team in self.drafted_players.values() for p in team):
                continue
                
            # Add player if no position filter or matches position
            if position is None or player.pos == position:
                available.append(player)
        
        # Sort by average rank, considering if we're using ML rankings
        if getattr(st.session_state, 'using_ml', False):
            # Sort by points (highest first) or position rank
            if getattr(st.session_state, 'show_position_ranks', False):
                # Group by position and sort within each position
                by_position = {}
                for p in available:
                    if p.pos not in by_position:
                        by_position[p.pos] = []
                    by_position[p.pos].append(p)
                
                # Sort each position group by points and assign ranks
                ranked_players = []
                for pos in by_position:
                    pos_players = by_position[pos]
                    pos_players.sort(key=lambda x: float(x.avg_rank), reverse=True)
                    for rank, player in enumerate(pos_players, 1):
                        player.pos_rank = rank
                    ranked_players.extend(pos_players)
                available = ranked_players
            else:
                available.sort(key=lambda x: float(x.avg_rank), reverse=True)  # Highest points first
        else:
            available.sort(key=lambda x: float(x.avg_rank))  # Lowest rank first
        
        # Return all players if top_n is None, otherwise return top_n players
        return available[:top_n] if top_n is not None else available

    def show_draft_board(self):
        """Display the current draft board"""
        draft_board = []
        total_picks = len(sum(self.drafted_players.values(), []))
        total_rounds = (total_picks // self.total_teams) + 1
        
        for round_num in range(1, total_rounds + 1):
            round_info = f"\nRound {round_num}:\n"
            draft_board.append(round_info)
            for pick_num in range(1, self.total_teams + 1):
                # Calculate the actual team number based on snake draft
                if round_num % 2 == 1:  # Odd rounds (1, 3, 5, etc.)
                    team_num = pick_num
                else:  # Even rounds (2, 4, 6, etc.)
                    team_num = self.total_teams - pick_num + 1
                
                # Use simple team label for draft board
                team_label = f"Team {team_num}"
                
                # Calculate the index in the team's draft list
                pick_index = round_num - 1
                team_picks = self.drafted_players[team_num]
                
                if pick_index < len(team_picks):
                    player = team_picks[pick_index]
                    pick_info = f"Pick {(round_num-1)*self.total_teams + pick_num}: {team_label} - {player.name} ({player.pos})\n"
                else:
                    pick_info = f"Pick {(round_num-1)*self.total_teams + pick_num}: {team_label} - --\n"
                draft_board.append(pick_info)
        
        return ''.join(draft_board)

    def get_team_info(self, team_number):
        """Display team information and needs"""
        # Add "Your Team" label if it's the user's team
        team_label = f"Team {team_number}"
        if team_number == self.your_position:
            team_label += " (Your Team)"
        
        roster = self.drafted_players.get(team_number, [])
        roster_display = [f"\n{team_label} Roster:"]  # Add team label at the top
        position_counts = {pos: 0 for pos in self.lineup_settings.keys()}

        for pos in position_counts.keys():
            pos_players = [p for p in roster if p.pos == pos]
            position_counts[pos] = len(pos_players)
            if pos_players:
                roster_display.append(f"{pos}: {', '.join(p.name for p in pos_players)}")
            else:
                roster_display.append(f"{pos}: None")

        # Calculate team needs
        needs_display = []
        for pos, count in position_counts.items():
            max_limit = self.roster_limits.get(pos, 0)
            remaining = max_limit - count
            if remaining > 0:
                needs_display.append(f"{pos} Needs: {remaining} more")

        return '\n'.join(roster_display) + "\n\n" + '\n'.join(needs_display)

    def get_best_available_by_position(self, position, top_n=None):
        available = []
        
        for player in self.available_players:
            # Skip if player is already drafted
            if any(p.name == player.name for team in self.drafted_players.values() for p in team):
                continue
                
            # Add player if matches position
            if player.pos == position:
                available.append(player)
        
        # Sort by average rank, considering if we're using ML rankings
        if getattr(st.session_state, 'using_ml', False):
            available.sort(key=lambda x: float(x.avg_rank), reverse=True)  # Highest points first
        else:
            available.sort(key=lambda x: float(x.avg_rank))  # Lowest rank first
        
        # Return all players if top_n is None, otherwise return top_n players
        return available[:top_n] if top_n is not None else available

    def get_team_needs(self, team_number):
        """Calculate team needs based on current roster and limits"""
        roster = self.drafted_players.get(team_number, [])
        needs = {}
        
        # Count current positions
        position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
        for player in roster:
            if player.pos in position_counts:
                position_counts[player.pos] += 1
        
        # Calculate needs based on roster limits
        for pos, count in position_counts.items():
            max_limit = self.roster_limits.get(pos, 0)
            if count < max_limit:
                needs[pos] = max_limit - count
        
        return needs

    def auto_draft_pick(self, team_number):
        """Make an automated draft pick for the given team"""
        team_needs = self.get_team_needs(team_number)
        if not team_needs:
            return False, "No team needs found"
        
        # Calculate current round
        total_picks = sum(len(players) for players in self.drafted_players.values())
        current_round = (total_picks // self.total_teams) + 1
        
        # Position priorities based on round
        if current_round <= 4:
            # First 4 rounds: Focus heavily on RB/WR
            position_weights = {
                'RB': 0.5,
                'WR': 0.4,
                'TE': 0.07,
                'QB': 0.03,
                'DST': 0,
                'K': 0
            }
        elif current_round <= 8:
            # Middle rounds: Start considering QB/TE more
            position_weights = {
                'RB': 0.35,
                'WR': 0.35,
                'TE': 0.15,
                'QB': 0.15,
                'DST': 0,
                'K': 0
            }
        elif current_round <= 13:
            # Later rounds: Consider all positions except K/DST
            position_weights = {
                'RB': 0.25,
                'WR': 0.25,
                'TE': 0.25,
                'QB': 0.25,
                'DST': 0,
                'K': 0
            }
        else:
            # Final rounds: K/DST priority
            position_weights = {
                'RB': 0.1,
                'WR': 0.1,
                'TE': 0.1,
                'QB': 0.1,
                'DST': 0.3,
                'K': 0.3
            }
        
        # Get candidates for each needed position
        candidates = []
        for pos in team_needs:
            if position_weights[pos] > 0:  # Only consider positions with weight > 0
                available = self.get_best_available_by_position(pos)
                if available:
                    # Take top players at each position
                    top_players = available[:3]
                    # Add position weight to each player
                    for player in top_players:
                        candidates.append((player, position_weights[pos]))
        
        if not candidates:
            # Fallback: take any player that fills a need
            for pos in team_needs:
                available = self.get_best_available_by_position(pos)
                if available:
                    candidates.append((available[0], 1))
        
        if not candidates:
            return False, "No suitable players found"
        
        # Select player using weighted random choice
        import random
        players, weights = zip(*candidates)
        
        # Adjust weights based on player ranking
        final_weights = []
        for player, base_weight in zip(players, weights):
            # Add some randomness but maintain ranking influence
            rank_factor = 1 / (float(player.avg_rank) + 1)  # Prevent division by zero
            final_weight = base_weight * rank_factor
            final_weights.append(final_weight)
        
        # Normalize weights
        total_weight = sum(final_weights)
        final_weights = [w/total_weight for w in final_weights]
        
        selected_player = random.choices(players, weights=final_weights, k=1)[0]
        return self.draft_player(selected_player.name, team_number)

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_user_data():
    """Load user data from JSON file"""
    data_file = Path('data_used/user_data.json')
    if data_file.exists():
        with open(data_file, 'r') as f:
            return json.load(f)
    return {'users': {}}

def save_user_data(data):
    """Save user data to JSON file"""
    with open('data_used/user_data.json', 'w') as f:
        json.dump(data, f)

def save_user_favorites(username, favorites):
    """Save user favorites to the JSON file"""
    data = load_user_data()
    data['users'][username]['favorites'] = list(favorites)
    save_user_data(data)

def save_user_busts(username, busts):
    """Save user favorites to the JSON file"""
    data = load_user_data()
    data['users'][username]['busts'] = list(busts)
    save_user_data(data)

def load_historical_data():
    """Load historical season data for players"""
    try:
        historical_qb_df = pd.read_csv('data_used/historical_seasons_pass.csv')
        historical_skill_df = pd.read_csv('data_used/historical_seasons_scrim.csv')
        
        # Combine the dataframes
        historical_df = pd.concat([historical_qb_df, historical_skill_df], ignore_index=True)
        return historical_df
    except FileNotFoundError as e:
        st.error(f"Error loading historical data: {e}")
        return pd.DataFrame()  # Return empty dataframe if files not found
    except Exception as e:
        st.error(f"Unexpected error loading historical data: {e}")
        return pd.DataFrame()

def main():
    # Initialize session state variables if they don't exist
    if 'page' not in st.session_state:
        st.session_state.page = "Main"
    
    # Initialize historical passing data
    if 'historical_passing' not in st.session_state:
        try:
            # Read CSV with proper column names
            st.session_state.historical_passing = pd.read_csv(
                'data_used/historical_seasons_pass.csv',
                dtype={
                    'Season': str,
                    'Player': str,
                    'Team': str,
                    'Pos': str
                }
            )
        except Exception as e:
            st.error(f"Error loading historical passing data: {e}")
            st.session_state.historical_passing = pd.DataFrame()
    
    # Initialize historical data
    if 'historical_data' not in st.session_state:
        try:
            st.session_state.historical_data = pd.read_csv('data_used/historical_seasons_scrim.csv')
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
            st.session_state.historical_data = pd.DataFrame()
    
    # Initialize player search results if not present
    if 'player_search_results' not in st.session_state:
        st.session_state.player_search_results = {}
    
    # Initialize session state for page and setup completion
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False
    if 'current_pick' not in st.session_state:
        st.session_state.current_pick = 1
    if 'matching_players' not in st.session_state:
        st.session_state.matching_players = []
    if 'selected_player' not in st.session_state:
        st.session_state.selected_player = None
    if 'team_names' not in st.session_state:
        st.session_state.team_names = {}
    if 'selected_stats_player' not in st.session_state:
        st.session_state.selected_stats_player = None
    if 'favorites' not in st.session_state:
        st.session_state.favorites = set()
    if 'busts' not in st.session_state:
        st.session_state.busts = set()
    if 'helper' not in st.session_state:
        st.session_state.helper = None
    if 'auto_drafting' not in st.session_state:
        st.session_state.auto_drafting = False

    # Show login/register page if not authenticated
    if not st.session_state.authenticated:
        st.title("Fantasy Football Draft Helper")
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                user_data = load_user_data()
                if username in user_data['users']:
                    if user_data['users'][username]['password'] == hash_password(password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        # Load user favorites
                        st.session_state.favorites = set(user_data['users'][username].get('favorites', []))
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("Username not found")

            # Add the "Continue as Guest" button
            if st.button("Continue as Guest"):
                st.session_state.authenticated = True
                st.session_state.username = "Guest"
                st.session_state.favorites = set()  # Initialize favorites for guest
                st.success("Continuing as Guest!")
                st.rerun()
        
        with tab2:
            st.header("Register")
            new_username = st.text_input("Username", key="register_username")
            new_password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.button("Register"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_data = load_user_data()
                    if new_username in user_data['users']:
                        st.error("Username already exists")
                    else:
                        user_data['users'][new_username] = {
                            'password': hash_password(new_password),
                            'favorites': []
                        }
                        save_user_data(user_data)
                        st.success("Registration successful! Please login.")
        
        return  # Don't proceed with the rest of the app if not authenticated

    # Add logout button in the sidebar
    with st.sidebar:
        if st.button("Logout"):
            # Reset all session state variables
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.page = "Setup"
            st.session_state.setup_complete = False
            st.session_state.current_pick = 1  # Reset current pick
            st.session_state.helper = None
            st.session_state.matching_players = []
            st.session_state.selected_player = None
            st.session_state.player_search_results = {}
            st.session_state.selected_stats_player = None
            st.rerun()
            
        # Add Back to Setup button only if setup is complete
        if st.session_state.setup_complete:
            if st.button("Back to Setup"):
                st.session_state.page = "Setup"
                st.session_state.setup_complete = False
                st.session_state.helper = None
                st.rerun()

    if st.session_state.page == "Setup":
        st.title("Fantasy Football Draft Helper")
        
        # Setup inputs in a horizontal layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_teams = st.number_input("Total Teams:", min_value=1, value=12)
        
        with col2:
            your_position = st.number_input("Your Draft Position:", min_value=1, value=1)
        
        with col3:
            total_rounds = st.number_input("Total Rounds:", min_value=1, value=15)

        # Starting lineup format
        st.subheader("Starting Lineup Format")
        lineup_settings = {}
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'FLEX']
        for pos in positions:
            default_value = 2 if pos in ['RB', 'WR'] else 1  # Set default to 2 for RB/WR
            lineup_settings[pos] = st.number_input(f"Starting {pos}:", min_value=0, value=default_value)

        # Roster limits
        st.subheader("Total Roster Limits")
        roster_limits = {}
        for pos in positions[:-1]:  # Exclude FLEX for roster limits
            default_value = 4 if pos in ['RB', 'WR'] else 2  # Set default to 4 for RB/WR
            roster_limits[pos] = st.number_input(f"Max {pos}:", min_value=0, value=default_value)

        # Add auto-draft option with timing
        auto_draft = st.checkbox("Enable Auto-Draft for CPU Teams", value=False)
        if auto_draft:
            cpu_pick_time = st.number_input("Seconds between CPU picks:", min_value=1, value=5)
            # Store the CPU pick time in session state
            st.session_state.cpu_pick_time = cpu_pick_time

        if st.button("Start Draft"):
            try:
                st.session_state.helper = DraftHelper(
                    total_teams, 
                    your_position, 
                    total_rounds, 
                    roster_limits, 
                    lineup_settings,
                    auto_draft=auto_draft
                )
                st.session_state.team_names = {i: f"Team {i}" for i in range(1, total_teams + 1)}
                st.success("Draft setup complete!")
                st.session_state.setup_complete = True
                st.session_state.page = "Main"
                st.rerun()
            except Exception as e:
                st.error(f"Error during setup: {e}")

    elif st.session_state.page == "Main":
        st.title("Fantasy Football Draft Helper")
        
        # Check if setup is complete and helper exists
        if not st.session_state.setup_complete or st.session_state.helper is None:
            st.error("Please complete setup first")
            st.session_state.page = "Setup"
            st.rerun()
            return

        # Calculate current team at the start
        current_team = st.session_state.helper.get_current_drafter(st.session_state.current_pick)

        # Create two columns for the main layout
        col1, col2 = st.columns(2)

        # Draft board and search in left column
        with col1:
            st.subheader("Draft Board")
            
            # Split the draft board text into rounds
            draft_board_text = st.session_state.helper.show_draft_board()
            rounds = draft_board_text.split('\n\n')
            
            # Calculate current round
            current_round = (st.session_state.current_pick - 1) // st.session_state.helper.total_teams + 1
            
            # Create an expander for each round, with the current and last round auto-expanded
            for i, round_text in enumerate(rounds, 1):
                if round_text.strip():  # Only process non-empty rounds
                    with st.expander(f"Round {i}", expanded=(i >= max(1, current_round - 1))):
                        st.text(round_text)
            
            # Always show search bar when auto-drafting is disabled or when it's user's turn
            if not st.session_state.helper.auto_draft or current_team == st.session_state.helper.your_position:
                st.subheader("Search Players")
                search_term = st.text_input("Search Player:", key="main_search")
                if search_term:
                    matching_players = st.session_state.helper.find_player(search_term)
                    if matching_players:
                        st.write("Search Results:")
                        for player in matching_players:
                            col1_search, col2_search = st.columns([4, 1])
                            indicators = ""
                            if player.name in st.session_state.favorites:
                                indicators += " ⭐"
                            if player.name in st.session_state.busts:
                                indicators += " 🚫"
                            with col1_search:
                                if getattr(st.session_state, 'using_ml', False):
                                    if getattr(st.session_state, 'show_position_ranks', False):
                                        st.write(f"{player.name}{indicators} ({player.pos}) - Position Rank: {getattr(player, 'pos_rank', 'N/A')}")
                                    else:
                                        st.write(f"{player.name}{indicators} ({player.pos}) - Projected Points: {player.avg_rank:.1f}")
                                else:
                                    st.write(f"{player.name}{indicators} ({player.pos}) - Rank: {int(player.avg_rank)}")
                            with col2_search:
                                if st.button(f"Draft", key=f"search_draft_{player.name}_{player.avg_rank}"):
                                    success, draft_result = st.session_state.helper.draft_player(player.name, current_team)
                                    if success:
                                        st.session_state.current_pick += 1
                                        st.session_state.matching_players = []
                                        st.rerun()

        # Best available in right column
        with col2:
            st.write(f"Current Team on the Clock: {st.session_state.team_names[current_team]}")
            
            # Create a container for draft messages
            message_container = st.empty()
            
            # Handle auto-draft only if it's enabled and it's not user's turn
            if (st.session_state.helper.auto_draft and 
                current_team != st.session_state.helper.your_position):
                st.session_state.auto_drafting = True
                
                # Add countdown if CPU pick time is >= 10 seconds
                if getattr(st.session_state, 'cpu_pick_time', 0) >= 10:
                    countdown = st.empty()
                    for i in range(st.session_state.cpu_pick_time, 0, -1):
                        countdown.write(f"CPU drafting in {i} seconds...")
                        time.sleep(1)
                    countdown.empty()
                else:
                    time.sleep(st.session_state.cpu_pick_time)
                
                success, result = st.session_state.helper.auto_draft_pick(current_team)
                if success:
                    message_container.success(f"Auto-drafted {result.name} ({result.pos}) to {st.session_state.team_names[current_team]}!")
                    st.session_state.current_pick += 1
                    time.sleep(1)
                    message_container.empty()
                    st.rerun()
                else:
                    message_container.error(f"Auto-draft failed: {result}")
            else:
                st.session_state.auto_drafting = False
                
                # Show best available section for all manual picks
                with st.container():
                    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
                    with header_col1:
                        st.subheader("Best Available Players")
                    with header_col2:
                        if st.button(
                            "↺",
                            help="Switch between Expert and Machine Learning Rankings",
                            type="secondary",
                            key="switch_rankings"
                        ):
                            st.session_state.using_ml = not getattr(st.session_state, 'using_ml', False)
                            success = st.session_state.helper.load_players('ml' if st.session_state.using_ml else 'expert')
                            if success:
                                message_container.success(f"Using {'ML' if st.session_state.using_ml else 'Expert'} Rankings")
                                st.rerun()
                            else:
                                message_container.error("Failed to load rankings")
                                st.session_state.using_ml = not st.session_state.using_ml
                    with header_col3:
                        if getattr(st.session_state, 'using_ml', False):
                            if st.button(
                                "📊",  # Changed to chart emoji icon
                                help="Toggle between Fantasy Points and Position Rankings",
                                type="secondary",
                                key="toggle_display_mode"
                            ):
                                st.session_state.show_position_ranks = not getattr(st.session_state, 'show_position_ranks', False)
                                st.rerun()

                    position = st.selectbox("Filter:", ['All','Favorites','Busts','QB', 'RB', 'WR', 'TE', 'K', 'DST'])
                    
                    best_available = []  # Initialize best_available list
                    if position == 'Favorites':
                        best_available = [p for p in st.session_state.helper.available_players 
                                        if p.name in st.session_state.favorites]
                        best_available.sort(key=lambda x: x.avg_rank)
                    elif position == 'Busts':
                        best_available = [p for p in st.session_state.helper.available_players 
                                        if p.name in st.session_state.busts]
                        best_available.sort(key=lambda x: x.avg_rank)
                    elif position == 'All': 
                        best_available = st.session_state.helper.get_best_available(top_n=10)
                    else:
                        best_available = st.session_state.helper.get_best_available_by_position(position, top_n=10)

                    if best_available:
                        for player in best_available:
                            col1, col2 = st.columns([4, 1])
                            # Add indicator for favorite and bust
                            indicators = ""
                            if player.name in st.session_state.favorites:
                                indicators += " ⭐"
                            if player.name in st.session_state.busts:
                                indicators += " 🚫"
                            with col1:
                                if getattr(st.session_state, 'using_ml', False):
                                    if getattr(st.session_state, 'show_position_ranks', False):
                                        st.write(f"{player.name}{indicators} ({player.pos}) - Position Rank: {getattr(player, 'pos_rank', 'N/A')}")
                                    else:
                                        st.write(f"{player.name}{indicators} ({player.pos}) - Projected Points: {player.avg_rank:.1f}")
                                else:
                                    st.write(f"{player.name}{indicators} ({player.pos}) - Rank: {int(player.avg_rank)}")
                            with col2:
                                if st.button(f"Draft", key=f"draft_{player.name}_{player.avg_rank}"):
                                    success, draft_result = st.session_state.helper.draft_player(player.name, current_team)
                                    if success:
                                        st.session_state.current_pick += 1
                                        st.session_state.matching_players = []
                                        st.rerun()
                    else:
                        if position == 'Favorites':
                            st.info("No available favorite players.")
                        else:
                            st.info(f"No available {position} players.")

        # Navigation buttons in a horizontal layout
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            if st.button("Go to Team Info"):
                st.session_state.page = "TeamInfo"
                st.rerun()
        with nav_col2:
            if st.button("Go to Player Stats"):
                st.session_state.page = "PlayerStats"
                st.rerun()
        with nav_col3:
            if st.button("Go to Favorites & Busts"):
                st.session_state.page = "FavBust"
                st.rerun()

    elif st.session_state.page == "TeamInfo":
        st.title("Team Information")
        
        # Create list of team names with "Your Team" label for the dropdown only
        team_options = []
        for team_num, team_name in st.session_state.team_names.items():
            if team_num == st.session_state.helper.your_position:
                team_options.append(f"{team_name} (Your Team)")
            else:
                team_options.append(team_name)
        
        # Team selection and information
        selected_team = st.selectbox("Select a team to view:", team_options)
        
        # Remove "(Your Team)" from selection to get the actual team number
        base_team_name = selected_team.split(" (Your Team)")[0]
        team_number = list(st.session_state.team_names.keys())[list(st.session_state.team_names.values()).index(base_team_name)]
        team_info_text = st.session_state.helper.get_team_info(team_number)
        
        # Display team info
        st.text_area("Team Info", team_info_text, height=300, disabled=True)

        # Rename Team
        new_team_name = st.text_input("Rename Team", value=base_team_name)
        if st.button("Rename Team"):
            st.session_state.team_names[team_number] = new_team_name
            st.success(f"Renamed to {new_team_name}")
            st.rerun()

        # Back button
        if st.button("Back to Main"):
            st.session_state.page = "Main"
            st.rerun()


    elif st.session_state.page == "FavBust":
        st.title("Manage Favorites & Busts")
        tab1, tab2 = st.tabs(["Favorites", "Busts"])

        # --- Favorites Tab ---
        with tab1:
            # Initialize search results in session state if not present
            if 'favorite_search_results' not in st.session_state:
                st.session_state.favorite_search_results = []
            st.subheader("Search Players to Favorite")
            col1, col2 = st.columns([4, 1])
            with col1:
                player_name = st.text_input("Enter Player Name:", key="favorite_search")
            with col2:
                search_clicked = st.button("Search", key="favorite_search_button")
            if search_clicked or (player_name and player_name != st.session_state.get('last_favorite_search', '')):
                st.session_state.last_favorite_search = player_name
                if player_name:
                    st.session_state.favorite_search_results = st.session_state.helper.find_player(player_name)
            if st.session_state.favorite_search_results:
                st.write("Search Results:")
                for player in st.session_state.favorite_search_results:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
                    with col2:
                        if player.name not in st.session_state.favorites:
                            if st.button("Favorite", key=f"fav_{player.name}_{player.avg_rank}"):
                                st.session_state.favorites.add(player.name)
                                if st.session_state.username != "Guest":
                                    save_user_favorites(st.session_state.username, st.session_state.favorites)
                                st.success(f"Added {player.name} to favorites!")
                                st.rerun()
                        else:
                            st.write("✓ Favorited")
            elif player_name:
                st.info("No players found.")
            st.subheader("Current Favorites")
            if st.session_state.favorites:
                favorite_players = []
                for player in st.session_state.helper.available_players:
                    if player.name in st.session_state.favorites:
                        favorite_players.append((player, "Available"))
                for team_num, team_players in st.session_state.helper.drafted_players.items():
                    for player in team_players:
                        if player.name in st.session_state.favorites:
                            team_name = st.session_state.team_names.get(team_num, f"Team {team_num}")
                            favorite_players.append((player, f"Drafted by {team_name}"))
                favorite_players.sort(key=lambda x: x[0].avg_rank)
                for player, status in favorite_players:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if getattr(st.session_state, 'using_ml', False):
                            st.write(f"{player.name} ({player.pos}) - Projected Points: {player.avg_rank:.1f} - {status}")
                        else:
                            st.write(f"{player.name} ({player.pos}) - Rank: {int(player.avg_rank)} - {status}")
                    with col2:
                        if st.button("Remove", key=f"remove_{player.name}_{player.avg_rank}"):
                            st.session_state.favorites.remove(player.name)
                            if st.session_state.username != "Guest":
                                save_user_favorites(st.session_state.username, st.session_state.favorites)
                            st.rerun()
            else:
                st.info("No players have been favorited yet.")

        # --- Busts Tab ---
        with tab2:
            if 'bust_search_results' not in st.session_state:
                st.session_state.bust_search_results = []
            st.subheader("Search Players to Bust")
            col1, col2 = st.columns([4, 1])
            with col1:
                player_name = st.text_input("Enter Player Name:", key="bust_search")
            with col2:
                search_clicked = st.button("Search", key="bust_search_button")
            if search_clicked or (player_name and player_name != st.session_state.get('last_bust_search', '')):
                st.session_state.last_bust_search = player_name
                if player_name:
                    st.session_state.bust_search_results = st.session_state.helper.find_player(player_name)
            if st.session_state.bust_search_results:
                st.write("Search Results:")
                for player in st.session_state.bust_search_results:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
                    with col2:
                        if player.name not in st.session_state.busts:
                            if st.button("Bust", key=f"bustpage_{player.name}_{player.avg_rank}"):
                                st.session_state.busts.add(player.name)
                                if st.session_state.username != "Guest":
                                    save_user_busts(st.session_state.username, st.session_state.busts)
                                st.success(f"Added {player.name} to busts!")
                                st.rerun()
                        else:
                            st.write("✓ Busted")
            elif player_name:
                st.info("No players found.")
            st.subheader("Current Busts")
            if st.session_state.busts:
                bust_players = []
                for player in st.session_state.helper.available_players:
                    if player.name in st.session_state.busts:
                        bust_players.append((player, "Available"))
                for team_num, team_players in st.session_state.helper.drafted_players.items():
                    for player in team_players:
                        if player.name in st.session_state.busts:
                            team_name = st.session_state.team_names.get(team_num, f"Team {team_num}")
                            bust_players.append((player, f"Drafted by {team_name}"))
                bust_players.sort(key=lambda x: x[0].avg_rank)
                for player, status in bust_players:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if getattr(st.session_state, 'using_ml', False):
                            st.write(f"{player.name} ({player.pos}) - Projected Points: {player.avg_rank:.1f} - {status}")
                        else:
                            st.write(f"{player.name} ({player.pos}) - Rank: {int(player.avg_rank)} - {status}")
                    with col2:
                        if st.button("Remove", key=f"remove_bust_{player.name}_{player.avg_rank}"):
                            st.session_state.busts.remove(player.name)
                            if st.session_state.username != "Guest":
                                save_user_busts(st.session_state.username, st.session_state.busts)
                            st.rerun()
            else:
                st.info("No players have been busted yet.")
        if st.button("Back to Main"):
            st.session_state.page = "Main"
            st.rerun()

    elif st.session_state.page == "PlayerStats":
        st.title("Player Stats Search")
        
        # Search section with both button and enter key functionality
        col1, col2 = st.columns([4, 1])
        with col1:
            player_name = st.text_input("Enter Player Name to Search:", key="stats_search")
        with col2:
            search_clicked = st.button("Search", key="stats_search_button")
        
        # Trigger search on either button click or enter key
        if search_clicked or (player_name and player_name != st.session_state.get('last_stats_search', '')):
            st.session_state.last_stats_search = player_name
            
            # Get historical data from session state
            historical_df = st.session_state.historical_data
            
            if historical_df.empty:
                st.error("Could not read player stats")
            else:
                # Search for player (case-insensitive)
                search_terms = player_name.lower().split()
                # Check if it's a QB (passing stats) or skill position player
                if 'Season' in historical_df.columns:  # QB data
                    player_col = historical_df.columns[-1]  # Player name is the last column
                else:  # Skill position data
                    player_col = 'Player'  # Player name column for skill positions
                
                mask = historical_df[player_col].str.lower().apply(
                    lambda x: all(term in str(x).lower() for term in search_terms)
                )
                results = historical_df[mask]
                
                if len(results) == 0:
                    st.info(f"No players found matching '{player_name}'")
                else:
                    # Group by player name
                    player_groups = results.groupby(player_col)
                    player_stats = {name: group.to_dict('records') for name, group in player_groups}
                    st.session_state.player_search_results = player_stats
                    
                    # Display player selection if multiple players found
                    if len(player_stats) > 1:
                        player_options = list(player_stats.keys())
                        selected_player = st.selectbox("Select Player:", player_options)
                        if selected_player:
                            display_player_stats(player_stats[selected_player])
                    else:
                        # Display stats for single player found
                        player_name = list(player_stats.keys())[0]
                        display_player_stats(player_stats[player_name])

        # Display existing search results if they exist
        elif st.session_state.player_search_results:
            if len(st.session_state.player_search_results) > 1:
                player_options = list(st.session_state.player_search_results.keys())
                selected_player = st.selectbox("Select Player:", player_options)
                if selected_player:
                    display_player_stats(st.session_state.player_search_results[selected_player])
            else:
                player_name = list(st.session_state.player_search_results.keys())[0]
                display_player_stats(st.session_state.player_search_results[player_name])

        # Back button
        if st.button("Back to Main"):
            st.session_state.page = "Main"
            st.rerun()

    elif st.session_state.page == "Stat Search":
        stat_search()

def display_player_stats(years_data):
    # Get player name based on data format
    if ' Player' in years_data[0]:
        player_name = years_data[0][' Player']
    else:
        player_name = list(years_data[0].keys())[-1]
    
    st.subheader(f"Career Statistics for {player_name}")
    
    # Check if it's a QB by looking at position
    is_qb = any(year.get(' Pos') == 'QB' for year in years_data if ' Pos' in year)
    
    if is_qb:
        passing_df = st.session_state.historical_passing
        
        # Create a dictionary to store unique seasons
        unique_seasons = {}
        for year_data in years_data:
            if year_data.get('Season'):
                season = str(int(year_data['Season']))
                if season not in unique_seasons:
                    unique_seasons[season] = year_data
        
        # Sort seasons in descending order
        sorted_seasons = sorted(unique_seasons.items(), key=lambda x: float(x[0]), reverse=True)
        
        for season, year_data in sorted_seasons:
            games = float(year_data.get(' G', 1)) or 1
            
            # Filter passing stats using correct column names
            filtered_df = passing_df[
                (passing_df['Season'].astype(str) == season) & 
                (passing_df['Player'].str.contains(player_name, case=False, na=False))
            ]
            
            pass_stats = filtered_df.to_dict('records')
            
            # Create a container for each season's stats
            with st.container():
                st.markdown(f"### {season} Season")
                st.write(f"Team: {year_data.get(' Team')}")
                st.write(f"Games: {year_data.get(' G')}, Starts: {year_data.get(' GS')}")
                
                # Display passing stats if available
                if pass_stats:
                    pass_data = pass_stats[0]
                    completions = float(pass_data['Cmp'])
                    attempts = float(pass_data['Att'])
                    pass_yards = float(pass_data['Yds'])
                    pass_tds = float(pass_data['TD'])
                    interceptions = float(pass_data['Int'])
                    rating = pass_data['Rate']
                    
                    # Calculate passing stats
                    pass_ypg = round(pass_yards / games, 1) if games > 0 else 0
                    yards_per_completion = round(pass_yards / completions, 1) if completions > 0 else 0
                    completion_percentage = round((completions / attempts * 100), 1) if attempts > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Passing Stats**")
                        st.write(f"Completions: {int(completions)}/{int(attempts)} ({completion_percentage}%)")
                        st.write(f"Passing Yards: {int(pass_yards)}")
                        st.write(f"Touchdowns: {int(pass_tds)}")
                        st.write(f"Interceptions: {int(interceptions)}")
                    
                    with col2:
                        st.write("**Efficiency**")
                        st.write(f"Yards per Completion: {yards_per_completion}")
                        st.write(f"Yards per Game: {pass_ypg}")
                        st.write(f"Passer Rating: {rating}")
                
                # Calculate rushing stats
                try:
                    rush_attempts = float(year_data.get(' Att', '0'))
                    rush_yards = float(year_data.get(' YScm', '0'))
                    rush_tds = float(year_data.get(' RRTD', '0'))
                except (ValueError, TypeError):
                    rush_attempts = 0
                    rush_yards = 0
                    rush_tds = 0
                
                rush_ypg = round(rush_yards / games, 1) if games > 0 else 0
                yards_per_rush = round(rush_yards / rush_attempts, 1) if rush_attempts > 0 else 0
                
                st.write("**Rushing Stats**")
                st.write(f"Carries: {int(rush_attempts)}, Yards: {int(rush_yards)}, TDs: {int(rush_tds)}")
                st.write(f"Yards per Carry: {yards_per_rush}, Yards per Game: {rush_ypg}")
                
                st.markdown("---")
    else:
        # Display non-QB stats, deduplicate by season
        unique_seasons = {}
        for year_data in years_data:
            season = year_data.get('Season')
            if season and season not in unique_seasons:
                unique_seasons[season] = year_data
        for season, year_data in sorted(unique_seasons.items(), key=lambda x: float(x[0]), reverse=True):
            if not year_data:
                continue
                
            games = float(year_data.get(' G', 1)) or 1
            
            with st.container():
                st.markdown(f"### {season} Season")
                st.write(f"Team: {year_data.get(' Team')}")
                st.write(f"Games: {year_data.get(' G')}, Starts: {year_data.get(' GS')}")
                
                # Calculate rushing/receiving stats
                try:
                    attempts = float(year_data.get(' Att', '0'))
                    yards = float(year_data.get(' Yds', '0'))
                    tds = float(year_data.get(' TD', '0'))
                    receptions = float(year_data.get(' Rec', '0'))
                    rec_yards = float(year_data.get(' RecYds', '0'))
                    rec_tds = float(year_data.get(' RecTD', '0'))
                except (ValueError, TypeError):
                    attempts = yards = tds = receptions = rec_yards = rec_tds = 0
                
                # Calculate per-game and efficiency stats
                rush_ypg = round(yards / games, 1) if games > 0 else 0
                yards_per_rush = round(yards / attempts, 1) if attempts > 0 else 0
                rec_ypg = round(rec_yards / games, 1) if games > 0 else 0
                yards_per_rec = round(rec_yards / receptions, 1) if receptions > 0 else 0
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Rushing Stats**")
                    st.write(f"Carries: {int(attempts)}")
                    st.write(f"Rushing Yards: {int(yards)}")
                    st.write(f"Rushing TDs: {int(tds)}")
                    st.write(f"Yards per Carry: {yards_per_rush}")
                    st.write(f"Rushing Yards per Game: {rush_ypg}")
                
                with col2:
                    st.write("**Receiving Stats**")
                    st.write(f"Receptions: {int(receptions)}")
                    st.write(f"Receiving Yards: {int(rec_yards)}")
                    st.write(f"Receiving TDs: {int(rec_tds)}")
                    st.write(f"Yards per Reception: {yards_per_rec}")
                    st.write(f"Receiving Yards per Game: {rec_ypg}")
                
                st.markdown("---")

def stat_search():
    st.title("Player Stat Search")
    
    # Get the historical data
    historical_df = st.session_state.historical_data
    
    if historical_df.empty:
        st.error("Historical data could not be loaded. Please check that the CSV files exist.")
        return
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        player_name = st.text_input("Player Name", "")
    
    with col2:
        positions = sorted(historical_df['FantPos'].unique().tolist())
        position = st.selectbox("Position", ["All"] + positions)
    
    with col3:
        years = sorted(historical_df['Year'].unique().tolist(), reverse=True)
        year = st.selectbox("Season", ["All"] + years)
    
    # Filter the data based on user inputs
    filtered_df = historical_df.copy()
    
    if player_name:
        filtered_df = filtered_df[filtered_df['Player'].str.contains(player_name, case=False)]
    
    if position != "All":
        filtered_df = filtered_df[filtered_df['FantPos'] == position]
    
    if year != "All":
        filtered_df = filtered_df[filtered_df['Year'] == year]
    
    # Display the filtered data
    if not filtered_df.empty:
        # Select relevant columns based on position
        if position == "QB" or (position == "All" and not filtered_df[filtered_df['FantPos'] == "QB"].empty):
            qb_cols = ['Player', 'Year', 'Tm', 'FantPos', 'G', 'GS', 'Cmp', 'Att', 'Yds', 'TD', 'Int', 
                      'RushAtt', 'RushYds', 'RushTD', 'PPR', 'PosRk']
            qb_df = filtered_df[filtered_df['FantPos'] == "QB"]
            if not qb_df.empty:
                st.subheader("Quarterback Stats")
                st.dataframe(qb_df[qb_cols].sort_values(by=['Year', 'PPR'], ascending=[False, False]))
        
        if position != "QB" or position == "All":
            skill_cols = ['Player', 'Year', 'Tm', 'FantPos', 'G', 'GS', 'Tgt', 'Rec', 'RecYds', 'RecTD',
                         'RushAtt', 'RushYds', 'RushTD', 'PPR', 'PosRk']
            skill_df = filtered_df[filtered_df['FantPos'] != "QB"]
            if not skill_df.empty:
                st.subheader("Skill Position Stats")
                st.dataframe(skill_df[skill_cols].sort_values(by=['Year', 'PPR'], ascending=[False, False]))

def search_player(name):
    # Convert search name to lowercase for case-insensitive comparison
    search_name = name.lower().strip()
    
    # Get all available data
    historical_passing = st.session_state.historical_passing
    historical_data = st.session_state.historical_data
    
    # Debug info
    st.write("Debug - Searching historical passing data:")
    if not historical_passing.empty:
        st.write(historical_passing['Player'].head())
    
    st.write("Debug - Searching historical data:")
    if not historical_data.empty:
        st.write(historical_data['Player'].head())
    
    # Search in both datasets
    matching_players_passing = historical_passing[
        historical_passing['Player'].str.lower().str.contains(search_name, na=False)
    ]
    
    matching_players_historical = historical_data[
        historical_data['Player'].str.lower().str.contains(search_name, na=False)
    ]
    
    # Combine results
    if not matching_players_historical.empty:
        return matching_players_historical.to_dict('records')
    elif not matching_players_passing.empty:
        return matching_players_passing.to_dict('records')
    
    return []

if __name__ == "__main__":
    main()