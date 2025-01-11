# fantasy_fb_gui_streamlit.py
import streamlit as st
import csv
import os
import json
from pathlib import Path
import hashlib

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
            # Use the current working directory
            rankings_path = os.path.join(os.getcwd(), 'data_used/rankings.csv')
            
            print(f"Looking for rankings file at: {rankings_path}")  # Debugging line
            
            if not os.path.exists(rankings_path):
                print("Rankings file not found.")  # Debugging line
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
        
        # Sort by average rank
        available.sort(key=lambda x: x.avg_rank)
        
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
                
                # Calculate the index in the team's draft list
                pick_index = round_num - 1
                team_picks = self.drafted_players[team_num]
                
                if pick_index < len(team_picks):
                    player = team_picks[pick_index]
                    pick_info = f"Pick {(round_num-1)*self.total_teams + pick_num}: Team {team_num} - {player.name} ({player.pos})\n"
                else:
                    pick_info = f"Pick {(round_num-1)*self.total_teams + pick_num}: Team {team_num} - --\n"
                draft_board.append(pick_info)
        
        return ''.join(draft_board)

    def get_team_info(self, team_number):
        """Display team information and needs"""
        roster = self.drafted_players.get(team_number, [])
        roster_display = []
        position_counts = {pos: 0 for pos in self.lineup_settings.keys()}  # Initialize position counts

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
                
            # Add player if no position filter or matches position
            if position is None or player.pos == position:
                available.append(player)
        
        # Sort by average rank
        available.sort(key=lambda x: x.avg_rank)
        
        # Return all players if top_n is None, otherwise return top_n players
        return available[:top_n] if top_n is not None else available

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
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    # Rest of your existing main() function code...

    if st.session_state.page == "Setup":
        st.title("Fantasy Football Draft Helper")
        
        # Setup inputs in a horizontal layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_teams = st.number_input("Total Teams:", min_value=1, value=12)
        
        with col2:
            your_position = st.number_input("Your Position:", min_value=1, value=1)
        
        with col3:
            total_rounds = st.number_input("Total Rounds:", min_value=1, value=15)

        # Starting lineup format
        st.subheader("Starting Lineup Format")
        lineup_settings = {}
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'FLEX']
        for pos in positions:
            lineup_settings[pos] = st.number_input(f"Starting {pos}:", min_value=0, value=1)

        # Roster limits
        st.subheader("Total Roster Limits")
        roster_limits = {}
        for pos in positions[:-1]:  # Exclude FLEX for roster limits
            roster_limits[pos] = st.number_input(f"Max {pos}:", min_value=0, value=2)

        if st.button("Start Draft"):
            try:
                st.session_state.helper = DraftHelper(total_teams, your_position, total_rounds, roster_limits, lineup_settings)
                st.session_state.team_names = {i: f"Team {i}" for i in range(1, total_teams + 1)}
                st.success("Draft setup complete!")
                st.session_state.setup_complete = True  # Mark setup as complete
                st.session_state.page = "Main"  # Redirect to main page
                st.rerun()  # Rerun the app to reflect the new page state
            except Exception as e:
                st.error(f"Error during setup: {e}")

    elif st.session_state.page == "Main":
        # ... existing code ...

        # Main draft interface
        st.title("Fantasy Football Draft Helper")

        # Create two columns for the main layout
        col1, col2 = st.columns(2)

        # Draft board in left column
        with col1:
            st.subheader("Draft Board")
            draft_board_text = st.session_state.helper.show_draft_board()
            st.text_area("Draft Board", value=draft_board_text, height=400, disabled=True)

        # Best available and draft controls in right column
        with col2:
            st.subheader("Best Available Players")
            position = st.selectbox("Filter:", ['All','Favorites','QB', 'RB', 'WR', 'TE', 'K', 'DST'])

            # Determine the current team based on the current pick
            current_team = st.session_state.helper.get_current_drafter(st.session_state.current_pick)

            # Calculate total picks
            total_picks = st.session_state.helper.total_teams * st.session_state.helper.total_rounds

            # Check if the draft is complete
            if st.session_state.current_pick > total_picks:
                st.warning("The draft has ended. No further drafting is allowed.")
                return  # Exit the main function to prevent further actions

            if position == 'Favorites':
                # Display favorited players that are still available
                favorite_players = [p for p in st.session_state.helper.available_players 
                                  if p.name in st.session_state.favorites]
                favorite_players.sort(key=lambda x: x.avg_rank)
                
                if favorite_players:
                    for player in favorite_players:
                        col1, col2 = st.columns([4, 1])  # Create two columns
                        with col1:
                            st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
                        with col2:
                            if st.button(f"Draft", key=f"draft_fav_{player.name}"):
                                success, draft_result = st.session_state.helper.draft_player(player.name, current_team)
                                if success:
                                    st.success(f"Drafted {draft_result.name} ({draft_result.pos}) to {st.session_state.team_names[current_team]}!")
                                    st.session_state.current_pick += 1
                                    st.session_state.matching_players = []
                                    st.rerun()
                else:
                    st.info("No available favorite players.")
            else:
                if position == 'All':
                    best_available = st.session_state.helper.get_best_available(top_n=10)
                else:
                    best_available = st.session_state.helper.get_best_available_by_position(position, top_n=10)
    
                for player in best_available:
                    col1, col2 = st.columns([4, 1])  # Create two columns
                    with col1:
                        st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
                    with col2:
                        if st.button(f"Draft", key=f"draft_{player.name}"):
                            success, draft_result = st.session_state.helper.draft_player(player.name, current_team)
                            if success:
                                st.success(f"Drafted {draft_result.name} ({draft_result.pos}) to {st.session_state.team_names[current_team]}!")
                                st.session_state.current_pick += 1
                                st.session_state.matching_players = []
                                st.rerun()
        
        # Draft controls below the columns
        st.subheader("Draft a Player")
        current_team = st.session_state.helper.get_current_drafter(st.session_state.current_pick)
        st.write(f"Current Team on the Clock: {st.session_state.team_names[current_team]}")

        # Create two columns for draft input
        draft_col1, draft_col2 = st.columns([2, 1])

        with draft_col1:
            player_name = st.text_input("Enter Player Name:", key="player_search")
            if st.button("Search Player"):
                st.session_state.matching_players = st.session_state.helper.find_player(player_name)
                if not st.session_state.matching_players:
                    st.info("No players found.")

        if st.session_state.matching_players:
            player_options = [f"{p.name} ({p.pos})" for p in st.session_state.matching_players]
            selected = st.selectbox("Select Player:", player_options)
    
            if st.button("Confirm Draft"):
                player_to_draft = next(p for p in st.session_state.matching_players 
                                    if f"{p.name} ({p.pos})" == selected)
                success, draft_result = st.session_state.helper.draft_player(player_to_draft.name, current_team)
                if success:
                    st.success(f"Drafted {draft_result.name} ({draft_result.pos}) to {st.session_state.team_names[current_team]}!")
                    st.session_state.current_pick += 1
                    st.session_state.matching_players = []
                    st.rerun()
            


       
        
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
        
        # Team selection and information
        selected_team = st.selectbox("Select a team to view:", list(st.session_state.team_names.values()))
        team_number = list(st.session_state.team_names.keys())[list(st.session_state.team_names.values()).index(selected_team)]
        team_info_text = st.session_state.helper.get_team_info(team_number)
        
        # Change this to a disabled text area
        st.text_area("Team Info", team_info_text, height=300, disabled=True)  # Updated to be non-editable

        # Rename Team
        new_team_name = st.text_input("Rename Team", value=selected_team)
        if st.button("Rename Team"):
            st.session_state.team_names[team_number] = new_team_name
            st.success(f"Renamed to {new_team_name}")
            st.rerun()  # Refresh to update the draft board

        # Back button
        if st.button("Back to Main"):
            st.session_state.page = "Main"
            st.rerun()


    elif st.session_state.page == "Favorites":
        st.title("Manage Favorite Players")
        
        # Search section
        st.subheader("Search Players to Favorite")
        player_name = st.text_input("Enter Player Name:")
        
        if player_name:  # Only show search results if there's input
            matching_players = st.session_state.helper.find_player(player_name)
            if not matching_players:
                st.info("No players found.")
            else:
                st.write("Search Results:")
                for player in matching_players:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{player.name} ({player.pos}) - Rank: {player.avg_rank}")
                    with col2:
                        # Only show favorite button if not already favorited
                        if player.name not in st.session_state.favorites:
                            if st.button("Favorite", key=f"fav_{player.name}"):
                                st.session_state.favorites.add(player.name)
                                save_user_favorites(st.session_state.username, st.session_state.favorites)
                                st.success(f"Added {player.name} to favorites!")
                                st.rerun()

                                # And when removing favorites:
                                if st.button("Remove", key=f"remove_{player.name}"):
                                    st.session_state.favorites.remove(player.name)
                                    save_user_favorites(st.session_state.username, st.session_state.favorites)
                                    st.rerun()
                        else:
                            st.write("✓ Favorited")

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
                    if st.button("Remove", key=f"remove_{player.name}"):
                        st.session_state.favorites.remove(player.name)
                        st.rerun()
        else:
            st.info("No players have been favorited yet.")

        if st.button("Back to Main"):
            st.session_state.page = "Main"
            st.rerun()

    elif st.session_state.page == "PlayerStats":
        st.title("Player Stats Search")
        player_name = st.text_input("Enter Player Name to Search:")
    
        if st.button("Search"):
            results = st.session_state.helper.search_player_stats(player_name)
            if results is None:
                st.error("Could not read player stats file")
            elif not results:
                st.info(f"No players found matching '{player_name}'")
            else:
                # Filter out drafted players and unranked players
                available_results = {}
                for player_name, player_stats in results.items():
                    # Check if player is in rankings database
                    is_ranked = any(p.name.lower() == player_name.lower() 
                                for p in st.session_state.helper.available_players)
                
                    # Check if player is already drafted
                    is_drafted = any(any(p.name.lower() == player_name.lower() 
                                    for p in team_players)
                                for team_players in st.session_state.helper.drafted_players.values())
                
                    if is_ranked and not is_drafted:
                        available_results[player_name] = player_stats
                    
            
                # Store only the filtered results
                st.session_state.player_search_results = available_results
                st.session_state.selected_stats_player = None

        if st.session_state.player_search_results:
            player_names = list(st.session_state.player_search_results.keys())
            if len(player_names) > 1:
                st.session_state.selected_stats_player = st.selectbox("Select a player:", player_names)
            else:
                st.session_state.selected_stats_player = player_names[0]

            if st.session_state.selected_stats_player:
                years_data = st.session_state.player_search_results[st.session_state.selected_stats_player]
                display_player_stats(years_data)

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