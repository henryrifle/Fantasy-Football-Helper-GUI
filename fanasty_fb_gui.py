import tkinter as tk
from tkinter import ttk, messagebox
from fanasty_fb import DraftHelper  # Import your existing DraftHelper class

class FantasyFootballGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fantasy Football Draft Helper")
        
        # Initialize basic variables
        self.helper = None
        self.current_pick = 1
        
        # Show setup dialog without loading rankings yet
        self.show_setup_dialog()

    def show_setup_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Draft Setup")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Basic setup frame
        basic_frame = ttk.LabelFrame(dialog, text="Basic Setup", padding="5")
        basic_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(basic_frame, text="Total Teams:").grid(row=0, column=0, padx=5, pady=5)
        total_teams = ttk.Entry(basic_frame)
        total_teams.grid(row=0, column=1, padx=5, pady=5)
        total_teams.insert(0, "12")
        
        ttk.Label(basic_frame, text="Your Position:").grid(row=1, column=0, padx=5, pady=5)
        your_pos = ttk.Entry(basic_frame)
        your_pos.grid(row=1, column=1, padx=5, pady=5)
        your_pos.insert(0, "1")
        
        ttk.Label(basic_frame, text="Total Rounds:").grid(row=2, column=0, padx=5, pady=5)
        total_rounds = ttk.Entry(basic_frame)
        total_rounds.grid(row=2, column=1, padx=5, pady=5)
        total_rounds.insert(0, "15")
        
        # Starting lineup frame
        lineup_frame = ttk.LabelFrame(dialog, text="Starting Lineup Format", padding="5")
        lineup_frame.pack(fill='x', padx=5, pady=5)
        
        lineup_entries = {}
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'FLEX']
        default_starters = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'K': 1, 'DST': 1, 'FLEX': 1}
        
        for i, pos in enumerate(positions):
            ttk.Label(lineup_frame, text=f"Starting {pos}:").grid(row=i, column=0, padx=5, pady=2)
            entry = ttk.Entry(lineup_frame, width=5)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, str(default_starters[pos]))
            lineup_entries[pos] = entry
        
        # Roster limits frame
        roster_frame = ttk.LabelFrame(dialog, text="Total Roster Limits", padding="5")
        roster_frame.pack(fill='x', padx=5, pady=5)
        
        roster_entries = {}
        bench_positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        default_limits = {'QB': 2, 'RB': 6, 'WR': 6, 'TE': 2, 'K': 1, 'DST': 1}
        
        for i, pos in enumerate(bench_positions):
            ttk.Label(roster_frame, text=f"Max {pos}:").grid(row=i, column=0, padx=5, pady=2)
            entry = ttk.Entry(roster_frame, width=5)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.insert(0, str(default_limits[pos]))
            roster_entries[pos] = entry
        
        def confirm():
            try:
                # Convert string inputs to integers
                total = int(total_teams.get())
                pos = int(your_pos.get())
                rounds = int(total_rounds.get())
                
                # Validate lineup settings
                lineup_settings = {}
                for pos_key, entry in lineup_entries.items():
                    try:
                        limit = int(entry.get())
                        if limit < 0:
                            messagebox.showerror("Error", f"{pos_key} starters cannot be negative")
                            return
                        lineup_settings[pos_key] = limit
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {pos_key} starters")
                        return
                
                # Validate roster limits
                roster_limits = {}
                for pos_key, entry in roster_entries.items():
                    try:
                        limit = int(entry.get())
                        if limit < lineup_settings.get(pos_key, 0):
                            messagebox.showerror("Error", 
                                f"Total {pos_key} limit must be at least equal to starting {pos_key}")
                            return
                        roster_limits[pos_key] = limit
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {pos_key} limit")
                        return
                
                # Validate position is within range
                if pos < 1 or pos > total:
                    messagebox.showerror("Error", "Your position must be between 1 and total teams")
                    return
                
                try:
                    self.helper = DraftHelper(total, pos, rounds, roster_limits, lineup_settings)
                    dialog.destroy()
                    self.initialize_main_ui()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                    dialog.destroy()
                    self.root.quit()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for teams, position, and rounds")
        
        ttk.Button(dialog, text="Start Draft", command=confirm).pack(pady=10)
        
        # Wait for dialog to close
        self.root.wait_window(dialog)

    def initialize_main_ui(self):
        """Initialize the main UI after setup"""
        if self.helper:
            # Create all frames first
            self.create_frames()
            
            # Create all widgets
            self.create_draft_controls()
            self.create_draft_board()
            self.create_team_info()
            
            # Only update displays after everything is created
            self.update_displays()

    def create_frames(self):
        """Create the main frames"""
        # Left frame
        self.left_frame = ttk.Frame(self.root, padding="10")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        # Middle frame
        self.middle_frame = ttk.Frame(self.root, padding="10")
        self.middle_frame.grid(row=0, column=1, sticky="nsew")
        
        # Right frame
        self.right_frame = ttk.Frame(self.root, padding="10")
        self.right_frame.grid(row=0, column=2, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def create_widgets(self):
        """Create all widgets at once"""
        # Left frame widgets - Draft Controls
        self.create_draft_controls()
        
        # Middle frame widgets - Draft Board
        self.create_draft_board()
        
        # Right frame widgets - Team Info and Best Available
        self.create_team_info()

    def create_draft_controls(self):
        # Header
        ttk.Label(self.left_frame, text="Draft Controls", font=('Arial', 14, 'bold')).pack(pady=5)
        
        # Current pick info
        self.pick_frame = ttk.Frame(self.left_frame)
        self.pick_frame.pack(fill='x', pady=5)
        self.pick_info = ttk.Label(self.pick_frame, text="")
        self.pick_info.pack()
        
        # Draft suggestions
        ttk.Label(self.left_frame, text="Draft Suggestions:", font=('Arial', 12, 'bold')).pack(pady=5)
        self.suggestions_text = tk.Text(
            self.left_frame, 
            height=15,           
            width=150,          # Increased from 100 to 150 for much wider display
            font=('Courier New', 11),
            wrap=tk.NONE        # Changed to NONE to prevent text wrapping
        )
        self.suggestions_text.pack(pady=5, expand=True, fill='both')  # Added expand and fill
        
        # Add horizontal scrollbar to suggestions
        h_scroll = ttk.Scrollbar(self.left_frame, orient='horizontal', command=self.suggestions_text.xview)
        h_scroll.pack(fill='x')
        
        # Add vertical scrollbar to suggestions
        v_scroll = ttk.Scrollbar(self.suggestions_text, orient='vertical', command=self.suggestions_text.yview)
        v_scroll.pack(side='right', fill='y')
        
        # Configure text widget to use both scrollbars
        self.suggestions_text.config(
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )
        
        # Draft player controls
        draft_frame = ttk.Frame(self.left_frame)
        draft_frame.pack(fill='x', pady=5)
        ttk.Label(draft_frame, text="Draft Player:", font=('Arial', 11)).pack(pady=5)
        self.draft_entry = ttk.Entry(draft_frame)
        self.draft_entry.pack(pady=5, fill='x', padx=5)
        ttk.Button(draft_frame, text="Draft Player", command=self.draft_player).pack(pady=5)
        
        # Add player search section with improved layout
        search_frame = ttk.LabelFrame(self.left_frame, text="Player Stats Search", padding="5")
        search_frame.pack(fill='x', pady=10, padx=5)
        
        # Search entry and button in a frame with proper spacing
        search_entry_frame = ttk.Frame(search_frame)
        search_entry_frame.pack(fill='x', padx=5, pady=5)
        
        self.search_entry = ttk.Entry(search_entry_frame)
        self.search_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        search_button = ttk.Button(search_entry_frame, 
                                  text="Search Stats", 
                                  command=self.show_player_stats,
                                  width=15)  # Fixed width for button
        search_button.pack(side='right', padx=(5, 0))

    def create_draft_board(self):
        ttk.Label(self.middle_frame, text="Draft Board", font=('Arial', 14, 'bold')).pack(pady=5)
        
        # Draft board with scrollbar
        board_frame = ttk.Frame(self.middle_frame)
        board_frame.pack(expand=True, fill='both')
        
        self.draft_board = tk.Text(board_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(board_frame, orient='vertical', command=self.draft_board.yview)
        self.draft_board.configure(yscrollcommand=scrollbar.set)
        
        self.draft_board.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')

    def create_team_info(self):
        # Team needs section
        ttk.Label(self.right_frame, text="Team Information", font=('Arial', 14, 'bold')).pack(pady=5)
        
        # Team management frame
        team_manage_frame = ttk.Frame(self.right_frame)
        team_manage_frame.pack(fill='x', pady=5)
        
        # Toggle button for names/numbers
        self.name_toggle_btn = ttk.Button(team_manage_frame, 
                                        text="Toggle Names/Numbers",
                                        command=self.toggle_team_display)
        self.name_toggle_btn.pack(side='left', padx=5)
        
        # Edit team names button
        ttk.Button(team_manage_frame, text="Edit Team Names",
                  command=self.show_team_name_editor).pack(side='left', padx=5)
        
        # Team selection frame
        team_select_frame = ttk.Frame(self.right_frame)
        team_select_frame.pack(fill='x', pady=5)
        
        ttk.Label(team_select_frame, text="Select Team:").pack(side='left', padx=5)
        self.team_var = tk.StringVar(value=str(self.helper.your_position))
        
        # Update team selection dropdown to use names when appropriate
        team_values = [str(i) for i in range(1, self.helper.total_teams + 1)]
        self.team_combo = ttk.Combobox(team_select_frame, textvariable=self.team_var, 
                                      values=team_values)
        self.team_combo.pack(side='left', padx=5)
        
        ttk.Button(team_select_frame, text="Show Team", 
                   command=self.show_selected_team).pack(side='left', padx=5)
        
        # Team info with scrollbar
        team_frame = ttk.Frame(self.right_frame)
        team_frame.pack(expand=True, fill='both', pady=5)
        
        self.team_info = tk.Text(team_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(team_frame, orient='vertical', command=self.team_info.yview)
        self.team_info.configure(yscrollcommand=scrollbar.set)
        
        self.team_info.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')
        
        # Best available controls - moved to bottom and given more space
        best_frame = ttk.Frame(self.right_frame)
        best_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(best_frame, text="Best Available Position:").pack(side='left')
        self.position_var = tk.StringVar(value="All")
        position_combo = ttk.Combobox(best_frame, textvariable=self.position_var, 
                                    values=["All", "QB", "RB", "WR", "TE", "K", "DST"],
                                    width=10)
        position_combo.pack(side='left', padx=5)
        
        # Give the button more width and ensure it's fully visible
        ttk.Button(best_frame, text="Show Best Available", 
                   command=self.show_best_available,
                   width=20).pack(side='left', padx=5)

    def update_displays(self):
        self.update_pick_info()
        self.update_suggestions()
        self.update_draft_board()
        self.update_team_info()

    def update_pick_info(self):
        drafting_team = self.helper.get_current_drafter(self.current_pick)
        next_pick = self.helper.get_next_pick_number(self.current_pick)
        
        info_text = f"Current Pick: {self.current_pick}\nDrafting Team: {drafting_team}"
        if drafting_team == self.helper.your_position:
            info_text += f"\nIT'S YOUR PICK!\nYour next pick will be: {next_pick}"
        
        self.pick_info.config(text=info_text)

    def update_suggestions(self):
        drafting_team = self.helper.get_current_drafter(self.current_pick)
        needs, _ = self.helper.get_team_needs(drafting_team)
        current_round = (self.current_pick - 1) // self.helper.total_teams + 1
        suggestions = self.helper.suggest_draft_pick(drafting_team, current_round, needs)
        
        self.suggestions_text.delete(1.0, tk.END)
        
        # Add header
        header = f"{'#':<3} {'Player':<35} {'POS':<6} {'Team':<8} {'Bye':<5} {'Rank':<8} {'Need':<8}\n"
        self.suggestions_text.insert(tk.END, header)
        self.suggestions_text.insert(tk.END, "-" * 75 + "\n")
        
        # Add each suggestion with priority
        for i, (player, priority) in enumerate(suggestions, 1):
            team = player.team if player.team else "--"
            bye = player.bye if player.bye else "--"
            line = f"{i:<3} {player.name:<35} {player.pos:<6} {team:<8} {bye:<5} {player.avg_rank:<8.1f} {priority:<8}\n"
            self.suggestions_text.insert(tk.END, line)

    def update_draft_board(self):
        self.draft_board.delete(1.0, tk.END)
        self.helper.show_draft_board()  # This prints to console
        
        # Get draft board text
        total_picks = len(sum(self.helper.drafted_players.values(), []))
        total_rounds = (total_picks // self.helper.total_teams) + 1
        
        for round_num in range(1, total_rounds + 1):
            self.draft_board.insert(tk.END, f"\nRound {round_num}:\n")
            for pick_num in range(1, self.helper.total_teams + 1):
                if round_num % 2 == 1:
                    team_num = pick_num
                else:
                    team_num = self.helper.total_teams - pick_num + 1
                
                team_identifier = self.helper.get_team_identifier(team_num)
                pick_index = round_num - 1
                team_picks = self.helper.drafted_players[team_num]
                
                if pick_index < len(team_picks):
                    player = team_picks[pick_index]
                    self.draft_board.insert(tk.END, 
                        f"Pick {(round_num-1)*self.helper.total_teams + pick_num}: "
                        f"{team_identifier} - {player.name} ({player.pos})\n")
                else:
                    self.draft_board.insert(tk.END,
                        f"Pick {(round_num-1)*self.helper.total_teams + pick_num}: "
                        f"{team_identifier} - --\n")

    def update_team_info(self):
        self.team_info.delete(1.0, tk.END)
        needs, roster = self.helper.get_team_needs(self.helper.your_position)
        
        # Team Needs Section with consistent formatting
        self.team_info.insert(tk.END, "Your Team Needs:\n")
        for pos, priority in needs:
            if pos in ['K', 'DST']:
                team_roster = self.helper.drafted_players[self.helper.your_position]
                has_position = any(p.pos == pos for p in team_roster)
                if has_position:
                    self.team_info.insert(tk.END, f"{pos}: Low (Already drafted)\n")
                else:
                    self.team_info.insert(tk.END, f"{pos}: High (Need 1)\n")
            else:
                self.team_info.insert(tk.END, f"{pos}: {priority}\n")
        
        # Current Roster Section with formatted display
        self.team_info.insert(tk.END, "\nYour Current Roster:\n")
        team_roster = self.helper.drafted_players[self.helper.your_position]
        
        # Group players by position
        positions = {'QB': [], 'RB': [], 'WR': [], 'TE': [], 'K': [], 'DST': []}
        for player in team_roster:
            positions[player.pos].append(player)
        
        # Display players by position group
        for pos in positions:
            if positions[pos]:  # Only show position if there are players
                self.team_info.insert(tk.END, f"\n{pos}:\n")
                for player in positions[pos]:
                    team_bye = f"{player.team} - Bye {player.bye}" if player.team and player.bye else "FA"
                    self.team_info.insert(tk.END, f"  {player.name} ({team_bye})\n")

    def draft_player(self):
        # Check if draft should end
        current_round = (self.current_pick - 1) // self.helper.total_teams + 1
        if current_round > self.helper.total_rounds:
            messagebox.showinfo("Draft Complete", "The draft has ended!")
            return
        
        player_name = self.draft_entry.get()
        if player_name:
            drafting_team = self.helper.get_current_drafter(self.current_pick)
            success, result = self.helper.draft_player(player_name, drafting_team)
            
            if success:
                player = result
                drafting_team = self.helper.get_current_drafter(self.current_pick)
                team_roster = self.helper.drafted_players[drafting_team]
                
                if player.pos in ['K', 'DEF']:
                    existing = any(p.pos == player.pos for p in team_roster)
                    if existing:
                        messagebox.showerror("Error", 
                            f"Team {drafting_team} already has a {player.pos}!")
                        return
                
                self.current_pick += 1
                self.draft_entry.delete(0, tk.END)
                self.update_displays()
                
                # Check if draft is complete after successful pick
                current_round = (self.current_pick - 1) // self.helper.total_teams + 1
                if current_round > self.helper.total_rounds:
                    messagebox.showinfo("Draft Complete", "The draft has ended!")
            else:
                if isinstance(result, list):
                    self.show_player_selection(result, drafting_team)
                else:
                    messagebox.showerror("Error", str(result))

    def show_player_selection(self, players, drafting_team):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Player")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Multiple matching players found:").pack(pady=5)
        
        for i, player in enumerate(players, 1):
            def make_select_command(p):
                return lambda: self.select_player(p, drafting_team, dialog)
            
            ttk.Button(dialog, 
                      text=f"{i}. {player.name} ({player.pos}) - Avg Rank: {player.avg_rank}",
                      command=make_select_command(player)).pack(pady=2)

    def select_player(self, player, drafting_team, dialog):
        success, _ = self.helper.draft_player(player.name, drafting_team)
        if success:
            self.current_pick += 1
            self.draft_entry.delete(0, tk.END)
            self.update_displays()
            dialog.destroy()

    def show_best_available(self):
        position = self.position_var.get()
        position = None if position == "All" else position
        
        # Create new window for best available players
        best_window = tk.Toplevel(self.root)
        best_window.title(f"Best Available {position if position else 'Players'}")
        best_window.geometry("600x800")  # Larger window
        
        # Configure grid
        best_window.grid_columnconfigure(0, weight=1)
        best_window.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ttk.Frame(best_window, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create text widget with scrollbar
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=('Courier New', 11))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout for text and scrollbar
        text_widget.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure main_frame grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Get all available players
        players = self.helper.get_best_available(position=position)
        
        if players:
            # Add header with bold font
            header = f"{'Rank':<6} {'Player':<35} {'POS':<6} {'Team':<6} {'Bye':<5} {'Avg':<8}\n"
            text_widget.insert(tk.END, header, 'bold')
            text_widget.insert(tk.END, "=" * 70 + "\n")  # Separator line
            
            # Configure bold tag
            text_widget.tag_configure('bold', font=('Courier New', 11, 'bold'))
            
            # Add players with consistent formatting
            for i, player in enumerate(players, 1):
                # Get team and bye week info (assuming these are stored in player object)
                team = getattr(player, 'team', '--')
                bye = getattr(player, 'bye', '--')
                
                line = f"{i:<6} {player.name:<35} {player.pos:<6} {team:<6} {bye:<5} {player.avg_rank:<8.1f}\n"
                text_widget.insert(tk.END, line)
        else:
            text_widget.insert(tk.END, "No players available for selected position")
        
        # Make text widget read-only
        text_widget.configure(state='disabled')
        
        # Center the window
        best_window.update_idletasks()
        width = best_window.winfo_width()
        height = best_window.winfo_height()
        x = (best_window.winfo_screenwidth() // 2) - (width // 2)
        y = (best_window.winfo_screenheight() // 2) - (height // 2)
        best_window.geometry(f'+{x}+{y}')

    def show_selected_team(self):
        try:
            # Extract team number from the selection
            team_str = self.team_var.get()
            team_num = int(team_str.split(':')[0] if ':' in team_str else team_str)
            
            needs, roster = self.helper.get_team_needs(team_num)
            team_identifier = self.helper.get_team_identifier(team_num)
            
            self.team_info.delete(1.0, tk.END)
            self.team_info.insert(tk.END, f"{team_identifier} Information:\n\n")
            
            # Team Needs Section
            self.team_info.insert(tk.END, "Team Needs:\n")
            for pos, priority in needs:
                self.team_info.insert(tk.END, f"{pos}: {priority}\n")
            
            # Current Roster Section with formatted display
            self.team_info.insert(tk.END, "\nCurrent Roster:\n")
            team_roster = self.helper.drafted_players[team_num]
            
            # Group players by position
            positions = {'QB': [], 'RB': [], 'WR': [], 'TE': [], 'K': [], 'DST': []}
            for player in team_roster:
                positions[player.pos].append(player)
            
            # Display players by position group
            for pos in positions:
                if positions[pos]:  # Only show position if there are players
                    self.team_info.insert(tk.END, f"\n{pos}:\n")
                    for player in positions[pos]:
                        team_bye = f"{player.team} - Bye {player.bye}" if player.team and player.bye else "FA"
                        self.team_info.insert(tk.END, f"  {player.name} ({team_bye})\n")
        except ValueError:
            messagebox.showerror("Error", "Please select a valid team number")

    def show_player_stats(self):
        player_name = self.search_entry.get().strip()
        if not player_name:
            messagebox.showwarning("Search Error", "Please enter a player name")
            return
        
        # Search for player stats
        results = self.helper.search_player_stats(player_name)
        
        if results is None:
            messagebox.showerror("Error", "Could not read player stats file")
            return
        
        if not results:
            messagebox.showinfo("Search Results", f"No players found matching '{player_name}'")
            return
        
        if len(results) > 1:
            # Create player selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Player")
            dialog.geometry("400x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Create scrollable frame
            canvas = tk.Canvas(dialog)
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            ttk.Label(scrollable_frame, text="Select a player:").pack(pady=5)
            
            # Add button for each player (not each year)
            for player_name, years_data in results.items():
                def make_select_command(years):
                    return lambda: self.display_player_stats(years, dialog)
                
                button_text = f"{player_name} ({years_data[0]['FantPos']} - {years_data[0]['Tm']})"
                ttk.Button(scrollable_frame, text=button_text,
                          command=make_select_command(years_data)).pack(pady=2)
            
            # Pack the scrollable frame
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        else:
            # If only one player found, show all their years
            player_name = list(results.keys())[0]
            years_data = results[player_name]
            self.display_player_stats(years_data)

    def display_player_stats(self, results, dialog=None):
        if dialog:
            dialog.destroy()
        
        # Create stats window
        stats_window = tk.Toplevel(self.root)
        player_name = results[0]['Player']
        stats_window.title(f"Career Stats: {player_name}")
        stats_window.geometry("1000x800")  # Larger window
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(stats_window, padding="10")
        main_frame.pack(expand=True, fill='both')
        
        # Create text widget with scrollbar
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=('Courier New', 11))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        text_widget.pack(side='left', expand=True, fill='both')
        scrollbar.pack(side='right', fill='y')
        
        # Configure tags for formatting
        text_widget.tag_configure('header', font=('Courier New', 13, 'bold'))
        text_widget.tag_configure('subheader', font=('Courier New', 11, 'bold'))
        text_widget.tag_configure('year_header', font=('Courier New', 12, 'bold'), foreground='blue')
        
        # Add player header
        text_widget.insert(tk.END, f"Career Statistics for {player_name}\n", 'header')
        text_widget.insert(tk.END, "=" * 80 + "\n\n")
        
        # Sort results by year (newest first)
        results.sort(key=lambda x: int(x['Year']), reverse=True)
        
        # Get position for consistent display
        position = results[0]['FantPos']
        
        # Create header based on position
        if position == 'QB':
            text_widget.insert(tk.END, f"{'Year':<6} {'Team':<5} {'G/GS':<8} "
                             f"{'Comp-Att':<12} {'Pass Yds':<10} {'TD':<4} {'INT':<4} "
                             f"{'Rush Yds':<10} {'Rush TD':<8} {'PPR':<6}\n", 'subheader')
        else:
            text_widget.insert(tk.END, f"{'Year':<6} {'Team':<5} {'G/GS':<8} "
                             f"{'Rush Att':<10} {'Rush Yds':<10} {'Rush TD':<8} "
                             f"{'Rec':<5} {'Rec Yds':<10} {'Rec TD':<7} {'PPR':<6}\n", 'subheader')
        
        text_widget.insert(tk.END, "-" * 80 + "\n")
        
        # Add stats for each year
        for player_data in results:
            year_data = []
            
            if position == 'QB':
                year_data = [
                    f"{player_data['Year']:<6}",
                    f"{player_data['Tm']:<5}",
                    f"{player_data['G']}/{player_data['GS']:<6}",
                    f"{player_data['Cmp']}-{player_data['Att']:<8}",
                    f"{player_data['Yds']:<10}",
                    f"{player_data['TD']:<4}",
                    f"{player_data['Int']:<4}",
                    f"{player_data['RushYds']:<10}",
                    f"{player_data['RushTD']:<8}",
                    f"{float(player_data['PPR']):.1f}"
                ]
            else:
                year_data = [
                    f"{player_data['Year']:<6}",
                    f"{player_data['Tm']:<5}",
                    f"{player_data['G']}/{player_data['GS']:<6}",
                    f"{player_data['RushAtt']:<10}",
                    f"{player_data['RushYds']:<10}",
                    f"{player_data['RushTD']:<8}",
                    f"{player_data['Rec']:<5}",
                    f"{player_data['RecYds']:<10}",
                    f"{player_data['RecTD']:<7}",
                    f"{float(player_data['PPR']):.1f}"
                ]
            
            text_widget.insert(tk.END, " ".join(year_data) + "\n")
        
        # Add career totals
        text_widget.insert(tk.END, "\nCareer Totals:\n", 'year_header')
        text_widget.insert(tk.END, "-" * 80 + "\n")
        
        # Calculate and display career totals
        games = sum(int(x['G']) for x in results)
        starts = sum(int(x['GS']) for x in results)
        ppr = sum(float(x['PPR']) for x in results)
        
        if position == 'QB':
            comp = sum(int(x['Cmp']) for x in results)
            att = sum(int(x['Att']) for x in results)
            pass_yds = sum(int(x['Yds']) for x in results)
            pass_td = sum(int(x['TD']) for x in results)
            ints = sum(int(x['Int']) for x in results)
            rush_yds = sum(int(x['RushYds']) for x in results)
            rush_td = sum(int(x['RushTD']) for x in results)
            
            text_widget.insert(tk.END, 
                f"Games: {games}  Starts: {starts}\n"
                f"Completions-Attempts: {comp}-{att}  ({(comp/att*100):.1f}%)\n"
                f"Passing Yards: {pass_yds:,}  TD: {pass_td}  INT: {ints}\n"
                f"Rushing Yards: {rush_yds:,}  Rush TD: {rush_td}\n"
                f"Career Fantasy Points: {ppr:.1f}\n"
            )
        else:
            rush_att = sum(int(x['RushAtt']) for x in results)
            rush_yds = sum(int(x['RushYds']) for x in results)
            rush_td = sum(int(x['RushTD']) for x in results)
            rec = sum(int(x['Rec']) for x in results)
            rec_yds = sum(int(x['RecYds']) for x in results)
            rec_td = sum(int(x['RecTD']) for x in results)
            
            text_widget.insert(tk.END, 
                f"Games: {games}  Starts: {starts}\n"
                f"Rush Att: {rush_att}  Rush Yds: {rush_yds:,}  Rush TD: {rush_td}\n"
                f"Rec: {rec}  Rec Yds: {rec_yds:,}  Rec TD: {rec_td}\n"
                f"Career Fantasy Points: {ppr:.1f}\n"
            )
        
        # Make text widget read-only
        text_widget.configure(state='disabled')
        
        # Center the window
        stats_window.update_idletasks()
        width = stats_window.winfo_width()
        height = stats_window.winfo_height()
        x = (stats_window.winfo_screenwidth() // 2) - (width // 2)
        y = (stats_window.winfo_screenheight() // 2) - (height // 2)
        stats_window.geometry(f'+{x}+{y}')

    def show_team_name_editor(self):
        """Show dialog to edit team names"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Team Names")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create scrollable frame
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create entry fields for each team
        team_entries = {}
        for i in range(1, self.helper.total_teams + 1):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill='x', pady=2, padx=5)
            
            ttk.Label(frame, text=f"Team {i}:").pack(side='left')
            entry = ttk.Entry(frame)
            entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
            entry.insert(0, self.helper.team_names.get(i, ""))
            team_entries[i] = entry
        
        def save_names():
            for team_num, entry in team_entries.items():
                name = entry.get().strip()
                if name:
                    self.helper.set_team_name(team_num, name)
            self.update_team_displays()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_names).pack(pady=10)
        
        # Pack the scrollable frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def toggle_team_display(self):
        """Toggle between team names and numbers"""
        self.helper.toggle_team_display()
        self.update_team_displays()

    def update_team_displays(self):
        """Update all displays that show team information"""
        # Update team combo values
        team_values = []
        for i in range(1, self.helper.total_teams + 1):
            identifier = self.helper.get_team_identifier(i)
            team_values.append(f"{i}: {identifier}" if self.helper.use_team_names else str(i))
        self.team_combo['values'] = team_values
        
        # Update current displays
        self.update_draft_board()
        self.update_pick_info()
        self.update_team_info()

def main():
    root = tk.Tk()
    app = FantasyFootballGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
