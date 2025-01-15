# fantasy_fb_gui_streamlit.py
import streamlit as st
import csv
import os
import json
from pathlib import Path
import hashlib
import time

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
            expert_rankings_path = os.path.join(os.getcwd(), 'data_used', 'rankings.csv')
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
            filename = 'rankings.csv' if ranking_type == 'expert' else 'flex.csv'
            rankings_path = os.path.join(os.getcwd(), 'data_used', filename)
            
            if not os.path.exists(rankings_path):
                print("Rankings file not found.")
                return False
            
            self.available_players = []  # Reset available players
            
            with open(rankings_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        player_name = row['Player']
                        
                        # Skip if we've already seen this player
                        if player_name.lower() in seen_players:
                            continue
                        
                        if ranking_type == 'ml':
                            # For ML rankings, verify player exists in expert rankings
                            player_pos = player_positions.get(player_name.lower())
                            if not player_pos:
                                continue  # Skip players not in expert rankings
                            # Only include RB, WR, TE for flex rankings
                            if player_pos not in ['RB', 'WR', 'TE']:
                                continue
                            try:
                                # Directly read the Predicted_FP value
                                rank_value = float(row['Predicted_FP'])
                                #print(f"Loading {player_name}: {rank_value}")
                            except ValueError:
                                continue
                        else:
                            # Expert rankings processing
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
        """Search for player stats in the CSV file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'data_used/fantasy_merged_7_17.csv')
            
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

def main():
    # Initialize session state for page and setup completion
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = "Setup"
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
    if 'player_search_results' not in st.session_state:
        st.session_state.player_search_results = {}
    if 'selected_stats_player' not in st.session_state:
        st.session_state.selected_stats_player = None
    if 'favorites' not in st.session_state:
        st.session_state.favorites = set()
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

    # Rest of your existing main() function code...

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
                            with col1_search:
                                st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
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
                    header_col1, header_col2 = st.columns([4, 1])
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

                    position = st.selectbox("Filter:", ['All','Favorites','QB', 'RB', 'WR', 'TE', 'K', 'DST'])
                    
                    best_available = []  # Initialize best_available list
                    if position == 'Favorites':
                        best_available = [p for p in st.session_state.helper.available_players 
                                        if p.name in st.session_state.favorites]
                        best_available.sort(key=lambda x: x.avg_rank)
                    elif position == 'All':
                        best_available = st.session_state.helper.get_best_available(top_n=10)
                    else:
                        best_available = st.session_state.helper.get_best_available_by_position(position, top_n=10)

                    if best_available:
                        for player in best_available:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                if getattr(st.session_state, 'using_ml', False):
                                    st.write(f"{player.name} ({player.pos}) - Projected Points: {player.avg_rank:.1f}")
                                else:
                                    st.write(f"{player.name} ({player.pos}) - Rank: {int(player.avg_rank)}")
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
        nav_col1, nav_col2,nav_col3= st.columns(3)
        with nav_col1:
            if st.button("Go to Team Info"):
                st.session_state.page = "TeamInfo"
                st.rerun()
        with nav_col2:
            if st.button("Go to Player Stats"):
                st.session_state.page = "PlayerStats"
                st.rerun()
        with nav_col3:
            if st.button("Go to Favorites"):
                st.session_state.page = "Favorites"
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


    elif st.session_state.page == "Favorites":
        st.title("Manage Favorite Players")
        
        # Initialize search results in session state if not present
        if 'favorite_search_results' not in st.session_state:
            st.session_state.favorite_search_results = []
        
        # Search section with both button and enter key functionality
        st.subheader("Search Players to Favorite")
        col1, col2 = st.columns([4, 1])
        with col1:
            player_name = st.text_input("Enter Player Name:", key="favorite_search")
        with col2:
            search_clicked = st.button("Search", key="favorite_search_button")
        
        # Trigger search on either button click or enter key
        if search_clicked or (player_name and player_name != st.session_state.get('last_favorite_search', '')):
            st.session_state.last_favorite_search = player_name
            if player_name:  # Only show search results if there's input
                st.session_state.favorite_search_results = st.session_state.helper.find_player(player_name)
        
        # Display search results
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

        # Current favorites section
        st.subheader("Current Favorites")
        if st.session_state.favorites:
            # Get all favorited players (both available and drafted)
            favorite_players = []
            
            # Check available players
            for player in st.session_state.helper.available_players:
                if player.name in st.session_state.favorites:
                    favorite_players.append((player, "Available"))
            
            # Check drafted players
            for team_num, team_players in st.session_state.helper.drafted_players.items():
                for player in team_players:
                    if player.name in st.session_state.favorites:
                        team_name = st.session_state.team_names.get(team_num, f"Team {team_num}")
                        favorite_players.append((player, f"Drafted by {team_name}"))
            
            # Sort by rank
            favorite_players.sort(key=lambda x: x[0].avg_rank)
            
            # Display favorites
            for player, status in favorite_players:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank} - {status}")
                with col2:
                    if st.button("Remove", key=f"remove_{player.name}_{player.avg_rank}"):
                        st.session_state.favorites.remove(player.name)
                        if st.session_state.username != "Guest":
                            save_user_favorites(st.session_state.username, st.session_state.favorites)
                        st.rerun()
        else:
            st.info("No players have been favorited yet.")

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
            results = st.session_state.helper.search_player_stats(player_name)
            if results is None:
                st.error("Could not read player stats file")
            elif not results:
                st.info(f"No players found matching '{player_name}'")
            else:
                st.session_state.player_search_results = results
                
                # Display player selection if multiple players found
                if len(results) > 1:
                    player_options = list(results.keys())
                    selected_player = st.selectbox("Select Player:", player_options)
                    if selected_player:
                        display_player_stats(results[selected_player])
                else:
                    # Display stats for single player found
                    player_name = list(results.keys())[0]
                    display_player_stats(results[player_name])

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

def display_player_stats(years_data):
    st.subheader(f"Career Statistics for {years_data[0]['Player']}")
    if years_data[0]['FantPos']!= "QB":
        for year_data in years_data:
            st.write(f"Year: {year_data['Year']}, Team: {year_data['Tm']}, Position: {year_data['FantPos']}")
            st.write(f"Games: {year_data['G']}, Starts: {year_data['GS']}, Fantasy Points: {year_data['PPR']}, Position Rank:{year_data['PosRk']}")
             # Calculate yards per game
            rush_yards = year_data.get('RushYds', 0) or 0
            rec_yards = year_data.get('RecYds', 0) or 0
            games = int(year_data['G']) if year_data['G'] else 1
            
            rush_ypg = round(float(rush_yards) / games, 1) if games > 0 else 0
            rec_ypg = round(float(rec_yards) / games, 1) if games > 0 else 0

            st.write(f"Carries:{year_data.get('RushAtt','N/A')},Rushing Yards: {year_data.get('RushYds', 'N/A')}, Rushing TDs: {year_data.get('RushTD', 'N/A')}")
            st.write(f"Yards per Carry: {year_data.get('YA', 'N/A')}, Yards per Game:{rush_ypg} ")
            st.write(f"Targets:{year_data.get('Tgt', 'N/A')}, Receptions:{year_data.get('Rec', 'N/A')}, Receiving Yards: {year_data.get('RecYds', 'N/A')}, Receiving TDs: {year_data.get('RecTD', 'N/A')}")
            st.write(f"Yards per Reception: {year_data.get('YR', 'N/A')}, Yards per Game:{rec_ypg} ")
            st.write("---")
    else:
        for year_data in years_data:
             # Calculate yards per game and completion
            pass_yards = year_data.get('Yds', 0) or 0
            completions = year_data.get('Cmp', 0) or 0
            games = int(year_data['G']) if year_data['G'] else 1
            
            pass_ypg = round(float(pass_yards) / games, 1) if games > 0 else 0
            yards_per_completion = round(float(pass_yards) / float(completions), 1) if float(completions) > 0 else 0

            # Rushing stats for QB
            rush_yards = year_data.get('RushYds', 0) or 0
            rush_ypg = round(float(rush_yards) / games, 1) if games > 0 else 0
            
            st.write(f"Year: {year_data['Year']}, Team: {year_data['Tm']}, Position: {year_data['FantPos']}")
            st.write(f"Games: {year_data['G']}, Starts: {year_data['GS']}, Fantasy Points: {year_data['PPR']}, Position Rank:{year_data['PosRk']}")
            st.write(f"Completions:{year_data.get('Cmp','N/A')},Attempts: {year_data.get('Att', 'N/A')}, Passing Yards: {year_data.get('Yds', 'N/A')},Touchdowns:{year_data.get('TD', 'N/A')},Interceptions:{year_data.get('Int', 'N/A')}")
            st.write(f"Yards per Completion:{yards_per_completion} , Yards per Game:{pass_ypg}")
            st.write(f"Fumbles: {year_data.get('Fmb', 'N/A')}, Fumbles Lost:{year_data.get('FL', 'N/A')}")
            st.write(f"Carries:{year_data.get('RushAtt','N/A')},Rushing Yards: {year_data.get('RushYds', 'N/A')}, Rushing TDs: {year_data.get('RushTD', 'N/A')}")
            st.write(f"Yards per Carry: {year_data.get('YA', 'N/A')}, Yards per Game:{rush_ypg} ")
            st.write("---")

if __name__ == "__main__":
    main()