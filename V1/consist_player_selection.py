
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Perceptron
from sklearn.metrics import accuracy_score

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

# Define target criteria
target_threshold_rushing = 1200  # Example threshold for rushing
years_required_rushing = 3  # Number of years a player must meet the target
age_cutoff_rushing =30

target_threshold_passing = 4600  # Example threshold for rushing
years_required_passing = 3  # Number of years a player must meet the target
age_cutoff_passing=32

target_threshold_receiving = 1300  # Example threshold for rushing
years_required_receiving = 3 # Number of years a player must meet the target
age_cutoff_receiving=30

# Count how many years each player meets the target criteria
rushing_data['Meets_Target'] = (rushing_data['rYds'] + rushing_data['rTD'] * 6) > target_threshold_rushing
consistency_rushing = rushing_data.groupby('Player').agg(
    Total_Years=('Meets_Target', 'sum'),
    Total_Yards=('rYds', 'sum'),
    Total_Touchdowns=('rTD', 'sum'),
    Current_Age=('Current_Age', 'last')  # Use the most recent current age
).reset_index()

# Filter players who meet the target for the required number of years and are below the age cutoff
consistent_rushing_players = consistency_rushing[
    (consistency_rushing['Total_Years'] >= years_required_rushing) & 
    (consistency_rushing['Current_Age'] <= age_cutoff_rushing)
]

# Display best players to draft for rushing based on consistency
print("Consistent Rushing Players to Draft:")
print(consistent_rushing_players[['Player', 'Total_Yards', 'Total_Touchdowns', 'Current_Age']].sort_values(by='Total_Yards', ascending=False))

# You can repeat similar logic for passing and receiving data
# For example, for passing data:
passing_data['Meets_Target'] = (passing_data['Yds'] + passing_data['TD'] * 6) > target_threshold_passing
consistency_passing = passing_data.groupby('Player').agg(
    Total_Years=('Meets_Target', 'sum'),
    Total_Yards=('Yds', 'sum'),
    Total_Touchdowns=('TD', 'sum'),
    Current_Age=('Current_Age', 'last')  # Use the most recent current age
).reset_index()

consistent_passing_players = consistency_passing[
    (consistency_passing['Total_Years'] >= years_required_passing) & 
    (consistency_passing['Current_Age'] <= age_cutoff_passing)
]

# Display best players to draft for passing based on consistency
print("Consistent Passing Players to Draft:")
print(consistent_passing_players[['Player', 'Total_Yards', 'Total_Touchdowns', 'Current_Age']].sort_values(by='Total_Yards', ascending=False))

# Similar logic can be applied for receiving data
receiving_data['Meets_Target'] = (receiving_data['RecYds'] + receiving_data['RecTD'] * 6) > target_threshold_receiving
consistency_receiving = receiving_data.groupby('Player').agg(
    Total_Years=('Meets_Target', 'sum'),
    Total_Yards=('RecYds', 'sum'),
    Total_Touchdowns=('RecTD', 'sum'),
    Current_Age=('Current_Age', 'last')  # Use the most recent current age
).reset_index()

consistent_receiving_players = consistency_receiving[
    (consistency_receiving['Total_Years'] >= years_required_receiving) & 
    (consistency_receiving['Current_Age'] <= age_cutoff_receiving)
]

# Display best players to draft for receiving based on consistency
print("Consistent Receiving Players to Draft:")
print(consistent_receiving_players[['Player', 'Total_Yards', 'Total_Touchdowns', 'Current_Age']].sort_values(by='Total_Yards', ascending=False))

