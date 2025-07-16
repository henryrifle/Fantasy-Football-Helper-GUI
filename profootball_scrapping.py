import requests
from bs4 import BeautifulSoup
import re
import csv
import re
import pandas as pd
import time

rootURL = 'https://www.pro-football-reference.com'
playerURL_list = []
player_list = []
qb_list = []
qb_url_list = []

url = 'https://www.pro-football-reference.com/years/2024/scrimmage.htm'   #for skilled positions players

url2 = 'https://www.pro-football-reference.com/years/2024/passing.htm'     #for quarterbacks

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}


#for quarterbacks

print("Clear existing Data ? Y/N")
clear_data = input()
if clear_data == "Y":
    clear_data = True
else:
    clear_data = False
#data cleaning for testing qb data
if clear_data == True:
    # Initialize the files with headers
    with open('data_used/train2.csv', 'w') as f:
        f.write('Player,Age,Team,Pos,G,GS,Cmp,Att,Cmp%,Yds,TD,TD%,Int,Int%,1D,Succ%,Lng,Y/A,AY/A,Y/C,Y/G,Rate,QBR,Sk,Yds_sack,Sk%,NY/A,ANY/A,4QC,GWD,FP\n')
    open('data_used/historical_seasons_pass.csv', 'w').close()

res2 = requests.get(url2, headers=headers)
print("Response Status Code:", res2.status_code)  # Check if the request was successful

soup2 = BeautifulSoup(res2.text,features="html.parser")

# Find all 'td' elements with the relevant class
for td in soup2.find_all('td', class_='left'):
    a_tag2 = td.find('a')
    if a_tag2:
        qb_list.append(a_tag2.text)  # Get player name
        qb_url_list.append(a_tag2['href'])  # Get player URL

# Output the results

qb_names = [name for name in qb_list if name not in [
    'PB','PHI', 'BAL', 'DET', 'ATL', 'CIN', 'GNB', 'IND', 'MIN', 'TAM', 'ARI', 
    'MIA', 'NOR', 'LAR', 'NYJ', 'CHI', 'JAX', 'DAL', 'PIT', 'HOU', 'TEN', 
    'SFO', 'WAS', 'NWE', 'LVR', 'KAN', 'BUF', 'DEN', 'SEA', 'LAC', 'CAR', 
    'NYG', 'CLE'] and not any(char.isdigit() for char in name)]

# Filter out any remaining entries that start with award designations
qb_names = [name for name in qb_names if not any(name.startswith(prefix) for prefix in ['AP', 'SB', 'MVP', 'ORoY', 'OPoY', 'CPoY'])]

#print("Player Names:", qb_names)
qb_urls = [i for i in qb_url_list if i.startswith('/players/')]
#print("Player URLs:", qb_urls)




counter2=0
df = pd.read_csv('data_used/train2.csv')
names_df = df[['Player']].dropna().reset_index(drop=True)


for qb_url in qb_urls:
    print(f"Current counter: {counter2}, Processing Player: {qb_url}")
    
    if qb_names[counter2] in names_df['Player'].values:
        print(f"Player {qb_url} already exists in the dataset. Skipping...")
        counter2 += 1
        continue
    else:
        print(f"Processing Player: {qb_url} | Amount left to process: {len(qb_urls) - counter2 - 1}")
        time.sleep(10)

        res2 = requests.get(rootURL + qb_url, headers=headers)
        if res2.status_code != 200:
            print(f"Failed to retrieve data for {qb_url}. Status code: {res2.status_code}")
            counter2 += 1
            continue

        # Reset final_df for the new player
        all_years_data = []
        final_df = pd.DataFrame()  # Reset DataFrame for new player

        soup2 = BeautifulSoup(res2.text, features="html.parser")
        # Find the table with rushing and receiving stats
        stats_table = soup2.find('table', id='passing') 
        if stats_table:
            # Get all rows from the table
            passing = stats_table.find_all('tr')  
            print("Number of rows found:", len(passing))
        else:
            print(f"No stats table found for {qb_url}. Skipping...")
            counter2 += 1
            continue  # Skip to the next player if no table is found

        data_stat_mapping = {
        'year_id': 'Season',               # Year of the data
        'age': 'Age',                       # Player's age
        'team_name_abbr': 'Team',          # Team abbreviation
        'pos': 'Pos',                       # Position (QB)
        'games': 'G',                       # Games played
        'games_started': 'GS',              # Games started
        'qb_rec': 'QBrec',                 # Quarterback record (wins-losses-ties)
        'pass_cmp': 'Cmp',                 # Completions
        'pass_att': 'Att',                 # Attempts
        'pass_cmp_pct': 'Cmp%',             # Completion percentage
        'pass_yds': 'Yds',                 # Passing yards
        'pass_td': 'TD',                   # Touchdowns
        'pass_td_pct': 'TD%',               # Touchdown percentage
        'pass_int': 'Int',                 # Interceptions
        'pass_int_pct': 'Int%',             # Interception percentage
        'pass_first_down': '1D',           # First downs
        'pass_success': 'Succ%',            # Success percentage
        'pass_long': 'Lng',                 # Longest pass
        'pass_yds_per_att': 'Y/A',         # Yards per attempt
        'pass_adj_yds_per_att': 'ANY/A',   # Adjusted net yards per attempt
        'pass_yds_per_cmp': 'Y/C',         # Yards per completion
        'pass_yds_per_g': 'Y/G',           # Yards per game
        'pass_rating': 'Rate',              # Passer rating
        'qbr': 'QBR',                      # Quarterback rating
        'pass_sacked': 'Sk',               # Sacks
        'pass_sacked_yds': 'Yds_sack',          # Yards lost to sacks
        'pass_sacked_pct': 'Sk%',          # Sack percentage
        'pass_net_yds_per_att': 'NY/A',    # Net yards per attempt
        'pass_adj_net_yds_per_att': 'ANY/A', # Adjusted net yards per attempt
        'comebacks': '4QC',                # Comebacks led
        'gwd': 'GWD',                      # Game-winning drives
        'av': 'AV',                        # Approximate Value
        'awards': 'Awards'                 # Awards received
        }

        
        
        
        # Format the data to match the headers and create a DataFrame for each year
        for row in passing:
            # Create a dictionary for this row's data
            formatted_row = {}
    
            # Loop through all td elements in the row
            for td in row.find_all(['td', 'th']):
                stat_name = td.get('data-stat')
                if stat_name in data_stat_mapping:
                    value = td.get_text(strip=True)
                    formatted_row[data_stat_mapping[stat_name]] = value
    
            # Only add rows that have data
            if formatted_row:  # Only append if the dictionary is not empty
                all_years_data.append(formatted_row)

        # Create DataFrame from all collected data
        final_df = pd.DataFrame()  # Reset DataFrame for new player
        final_df = pd.DataFrame(all_years_data)

        # Drop rows where all columns are NA
        final_df = final_df.dropna(how='all')

        # Filter out summary rows by requiring Age, Team, or Lg to have a value
        final_df = final_df[final_df[['Age', 'Team']].notna().any(axis=1)]

        # Assuming 'df' is your DataFrame
        final_df = final_df.drop(index=0).reset_index(drop=True)
        # Check if 'QBrec' and 'Awards' exist in the DataFrame before dropping
        columns_to_drop = ["Awards", "QBrec"]
        final_df = final_df.drop(columns=[col for col in columns_to_drop if col in final_df.columns], axis=1)
        final_df['Player'] = qb_names[counter2]

        

        
        # Check the columns in final_df
        #print("Columns in final_df:", final_df.columns)

        # Update numeric conversion with a safe access method
        numeric_columns = ["G","GS","Cmp","Att","Cmp%","Yds","TD","TD%","Int","Int%","1D","Succ%","Lng","Y/A","AY/A","Y/C","Y/G","Rate","QBR","Sk","Yds_sack","Sk%","NY/A","ANY/A","4QC","GWD"]
        for col in numeric_columns:
            if col in final_df.columns:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            else:
                print(f"Column '{col}' does not exist in final_df.")

        # Drop rows where all columns are NA
        final_df = final_df.dropna(how='all')
        # Summarize career statistics
        columns_to_summarize = [
            'G', 'GS', 'Cmp', 'Att', 'Cmp%', 'Yds', 'TD', 'TD%', 'Int', 'Int%', 
            '1D', 'Succ%', 'Lng', 'Y/A', 'AY/A', 'Y/C', 'Y/G', 'Rate', 
            'QBR', 'Sk', 'Yds_sack', 'Sk%', 'NY/A', 'ANY/A', '4QC', 'GWD'
        ]
        print(final_df.head)
        final_df.to_csv("data_used/historical_seasons_pass.csv",mode='a',header=False,index=False)
        # Initialize career_stats with the first row for Season, Age, Team, Pos
        if len(final_df) > 0:
            career_stats = final_df[['Player', 'Age', 'Team', 'Pos']].iloc[len(final_df)-1]
            
            # Loop through the columns and calculate the mean if the column exists
            for col in columns_to_summarize:
                if col in final_df.columns:
                    career_stats[col] = final_df[col].mean()  # Calculate mean
                else:
                    career_stats[col] = None  # Set to None if the column does not exist

            career_stats['FP'] = (career_stats['Yds'] * 0.04)+(career_stats['TD']*6)-(career_stats['Int']*2)

            # Convert the Series to a DataFrame
            career_stats_df = pd.DataFrame(career_stats).T
            career_stats_df.to_csv('data_used/train2.csv', mode='a',header=False,index=False)
        else:
            print(f"No valid data found for player {qb_names[counter2]}, skipping...")
        
        counter2 += 1  # Ensure this is executed at the end of processing



"""""
#for rushing and recieving




## Scrape for table data
res = requests.get(url, headers=headers)
print("Response Status Code:", res.status_code)  # Check if the request was successful

soup = BeautifulSoup(res.text,features="html.parser")

# Find all 'td' elements with the relevant class
for td in soup.find_all('td', class_='left'):
    a_tag = td.find('a')
    if a_tag:
        player_list.append(a_tag.text)  # Get player name
        playerURL_list.append(a_tag['href'])  # Get player URL

# Output the results
player_names = [name for name in player_list if name not in [
    'PB','PHI', 'BAL', 'DET', 'ATL', 'CIN', 'GNB', 'IND', 'MIN', 'TAM', 'ARI', 
    'MIA', 'NOR', 'LAR', 'NYJ', 'CHI', 'JAX', 'DAL', 'PIT', 'HOU', 'TEN', 
    'SFO', 'WAS', 'NWE', 'LVR', 'KAN', 'BUF', 'DEN', 'SEA', 'LAC', 'CAR', 
    'NYG', 'CLE'] and not any(char.isdigit() for char in name)]

# Filter out any remaining entries that start with award designations
player_names = [name for name in player_names if not any(name.startswith(prefix) for prefix in ['AP', 'SB', 'MVP', 'ORoY', 'OPoY', 'CPoY'])]

#print("Player Names:", player_names)
player_urls = [i for i in playerURL_list if i.startswith('/players/')]
#print("Player URLs:", player_urls)


counter=0
df = pd.read_csv('data_used/train.csv')
names_df = df[['Player']].dropna().reset_index(drop=True)


for player_url in player_urls:
    print(f"Current counter: {counter}, Processing Player: {player_url}")
    
    if player_names[counter] in names_df['Player'].values:
        print(f"Player {player_url} already exists in the dataset. Skipping...")
        counter += 1
        continue
    else:
        print(f"Processing Player: {player_url} | Amount left to process: {len(player_urls) - counter - 1}")
        time.sleep(10)

        res2 = requests.get(rootURL + player_url, headers=headers)
        if res2.status_code != 200:
            print(f"Failed to retrieve data for {player_url}. Status code: {res2.status_code}")
            counter += 1
            continue

        # Reset final_df for the new player
        all_years_data = []
        
        final_df = pd.DataFrame()  # Reset DataFrame for new player
        

        soup2 = BeautifulSoup(res2.text, features="html.parser")

        # Find the table with rushing and receiving stats
        stats_table = soup2.find('table', id='receiving_and_rushing') or soup2.find('table', id='rushing_and_receiving')
        if stats_table:
            # Get all rows from the table
            rushing_receiving = stats_table.find_all('tr')  
            print("Number of rows found:", len(rushing_receiving))
        else:
            print(f"No stats table found for {player_url}. Skipping...")
            counter += 1
            continue  # Skip to the next player if no table is found

        # Define the mapping from data-stat to desired column names
        data_stat_mapping = {
            'year_id': 'Season',
            'age': 'Age',
            'team_name_abbr': 'Team',
            'comp_name_abbr': 'Lg',
            'pos': 'Pos',
            'games': 'G',
            'games_started': 'GS',
            'rush_att': 'Att',
            'rush_yds': 'Yds',
            'rush_td': 'TD',
            'rush_first_down': '1D',
            'rush_success': 'Succ%',
            'rush_long': 'Lng',
            'rush_yds_per_att': 'Y/A',
            'rush_yds_per_g': 'Y/G',
            'rush_att_per_g': 'A/G',
            'targets': 'Tgt',
            'rec': 'Rec',
            'rec_yds': 'Yds',
            'rec_yds_per_rec': 'Y/R',
            'rec_td': 'TD',  # Note: This is repeated
            'rec_first_down': '1D',  # Note: This is repeated
            'rec_success': 'Succ%',
            'rec_long': 'Lng',
            'rec_per_g': 'R/G',
            'rec_yds_per_g': 'Y/G',
            'catch_pct': 'Ctch%',
            'rec_yds_per_tgt': 'Y/Tgt',
            'touches': 'Touch',
            'yds_per_touch': 'Y/Tch',
            'yds_from_scrimmage': 'YScm',
            'rush_receive_td': 'RRTD',
            'fumbles': 'Fmb',
            'av': 'AV',
        }

        # Format the data to match the headers and create a DataFrame for each year
        for row in rushing_receiving:
            # Skip header rows
            if row.get('class') and 'thead' in row.get('class'):
                continue
            
            # Create a dictionary for this row's data
            formatted_row = {}
            
            # Loop through all td elements in the row
            for td in row.find_all(['td', 'th']):
                stat_name = td.get('data-stat')
                
                # Skip any award-related data stats
                if stat_name in ['awards', 'player-additional']:
                    continue
                    
                if stat_name in data_stat_mapping:
                    value = td.get_text(strip=True)
                    # Remove any award text that might be in the value
                    if value and any(award in value for award in ['AP', 'PB', 'AP1', 'AP2']):
                        value = value.split(' ')[0]  # Take only the first part before any award text
                    formatted_row[data_stat_mapping[stat_name]] = value

            # Only add rows that have data and are not header rows
            if formatted_row and not all(v in data_stat_mapping.values() for v in formatted_row.values()):
                all_years_data.append(formatted_row)

        # Create DataFrame from all collected data
        
        final_df = pd.DataFrame()  # Reset DataFrame for new player
        final_df = pd.DataFrame(all_years_data)
        

        # Drop rows where all columns are NA
        final_df = final_df.dropna(how='all')

        # Filter out summary rows by requiring Age, Team, or Lg to have a value
        final_df = final_df[final_df[['Age', 'Team', 'Lg']].notna().any(axis=1)]
        
    

        # Assuming 'df' is your DataFrame
        final_df = final_df.drop(index=0).reset_index(drop=True)
        # Check if 'AV' exists in the DataFrame before dropping
        if 'AV' in final_df.columns:
            final_df = final_df.drop([ "AV", "Lg"], axis=1)
        else:
            final_df = final_df.drop([ "Lg"], axis=1)  # Drop only the columns that exist
        final_df['Player'] = player_names[counter]
        
        

        # Check the columns in final_df
        #print("Columns in final_df:", final_df.columns)

        # Update numeric conversion with a safe access method
        numeric_columns = ['G', 'GS', 'Att', 'Yds', 'TD', 'Rec', 'Y/R', 'Tgt', 'Touch', 'YScm', 'RRTD', 'Fmb']
        for col in numeric_columns:
            if col in final_df.columns:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            else:
                print(f"Column '{col}' does not exist in final_df.")

        # Drop rows where all columns are NA
        final_df = final_df.dropna(how='all')
        # Summarize career statistics
        columns_to_summarize = [
            'G', 'GS', 'Att', 'Yds', 'TD', 'Rec', 'Y/R', 'Tgt', 'Touch', 'YScm', 'RRTD', 'Fmb'
        ]
        
        final_df.to_csv("data_used/historical_seasons_scrim.csv",mode='a',header=False,index=False)
        # Initialize career_stats with the first row for Season, Age, Team, Pos
        if len(final_df) > 0:
            career_stats = final_df[['Player', 'Age', 'Team', 'Pos']].iloc[len(final_df)-1]
            
            # Loop through the columns and calculate the mean if the column exists
            for col in columns_to_summarize:
                if col in final_df.columns:
                    career_stats[col] = final_df[col].mean()  # Calculate mean
                else:
                    career_stats[col] = None  # Set to None if the column does not exist

            career_stats['FP'] = (career_stats['YScm'] * 0.1)+(career_stats['Rec']*1)+(career_stats['RRTD']*6)+(career_stats['Fmb']*-2)

            # Convert the Series to a DataFrame
            career_stats_df = pd.DataFrame(career_stats).T
            career_stats_df.to_csv('data_used/train.csv', mode='a',header=False,index=False)
        else:
            print(f"No valid data found for player {player_names[counter]}, skipping...")
        
        counter += 1  # Ensure this is executed at the end of processing

"""""














    