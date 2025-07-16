import numpy as np
import pandas as pd

# Load data
rushing_data = pd.read_csv('rushing_cleaned.csv')
passing_data = pd.read_csv('passing_cleaned.csv')
receiving_data = pd.read_csv('fantasy_merged_7_17.csv')
rankings = pd.read_csv('rankings.csv')

# Define the current year for age calculation
current_year = 2025  # Update this to the current season year

# Data cleaning and feature engineering
# Example: Create a new feature for average yards per game
rushing_data = rushing_data.drop(columns=["r1D", "rLng"])
passing_data = passing_data.drop(columns=["1D","Lng","Sk","Yds-s","Sk%","NY/A","ANY/A"])
receiving_data = receiving_data.drop(columns=["Cmp","Att","Yds","TD","Int","RushAtt","RushYds","YA","RushTD","PPR","PlayerID","PosRk"])
receiving_data=receiving_data.rename(columns={"FantPos":"Pos"})
# Ensure that the "Player" columns are of the same type (string)
rushing_data["Player"] = rushing_data["Player"].astype(str)
passing_data["Player"] = passing_data["Player"].astype(str)
receiving_data["Player"] = receiving_data["Player"].astype(str)
rankings["Player"] = rankings["Player"].astype(str)

# Assuming the dataset has a 'Year' column indicating the season year
# Example: rushing_data['Year'] = [2021, 2022, 2023, ...]

# Filter out players not in rankings
rushing_data = rushing_data[rushing_data["Player"].isin(rankings["Player"])]
passing_data = passing_data[passing_data["Player"].isin(rankings["Player"])]
receiving_data = receiving_data[receiving_data["Player"].isin(rankings["Player"])]

# Filter out players with zero rushing yards
rushing_data = rushing_data[rushing_data['rYds'] > 0]

# Filter out players with zero passing yards
passing_data = passing_data[passing_data['Yds'] > 0]

# Filter out players with zero receiving yards
receiving_data = receiving_data[receiving_data['RecYds'] > 0]

# Calculate current age based on the year of the season played
rushing_data['Current_Age'] = rushing_data['Age'] + (current_year - rushing_data['Year'])
passing_data['Current_Age'] = passing_data['Age'] + (current_year - passing_data['Year'])
receiving_data['Current_Age'] = receiving_data['Age'] + (current_year - receiving_data['Year'])

# Define criteria for breakout players
age_cutoff_breakout = 25  # Example age cutoff for breakout players
max_years_played = 3  # Maximum number of years in the league
target_threshold_rushing = 800  # Example threshold for rushing yards
target_threshold_passing = 3000  # Example threshold for passing yards
target_threshold_receiving = 800  # Example threshold for receiving yards

# Identify potential breakout rushing players
breakout_rushing_players = rushing_data[
    (rushing_data['Current_Age'] < age_cutoff_breakout) & 
    ((current_year - rushing_data['Year']) <= max_years_played) &
    (rushing_data['rYds'] > target_threshold_rushing)
]

print("Potential Breakout Rushing Players:")
print(breakout_rushing_players[['Player', 'Current_Age', 'rYds', 'rTD']].sort_values(by='rYds', ascending=False))

# Identify potential breakout passing players
breakout_passing_players = passing_data[
    (passing_data['Current_Age'] < age_cutoff_breakout) & 
    ((current_year - passing_data['Year']) <= max_years_played) &
    (passing_data['Yds'] > target_threshold_passing)
]

print("\nPotential Breakout Passing Players:")
print(breakout_passing_players[['Player', 'Current_Age', 'Yds', 'TD']].sort_values(by='Yds', ascending=False))

# Identify potential breakout receiving players
breakout_receiving_players = receiving_data[
    (receiving_data['Current_Age'] < age_cutoff_breakout) & 
    ((current_year - receiving_data['Year']) <= max_years_played) &
    (receiving_data['RecYds'] > target_threshold_receiving)
]

print("\nPotential Breakout Receiving Players:")
print(breakout_receiving_players[['Player', 'Current_Age', 'RecYds', 'RecTD']].sort_values(by='RecYds', ascending=False))

