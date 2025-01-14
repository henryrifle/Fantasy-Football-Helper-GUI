import requests
from bs4 import BeautifulSoup
import re
import csv
import re
import pandas as pd

rootURL = 'https://www.pro-football-reference.com'
playerURL_list = []
player_list = []

url = 'https://www.pro-football-reference.com/years/2024/scrimmage.htm'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

## Scrape for table data
res = requests.get(url, headers=headers)
print("Response Status Code:", res.status_code)  # Check if the request was successful
print("Response Content:", res.text[:500])  # Print the first 500 characters of the response

soup = BeautifulSoup(res.text,features="html.parser")


rows = soup.findAll('td')



# Find all 'td' elements with the relevant class
for td in soup.find_all('td', class_='left'):
    a_tag = td.find('a')
    if a_tag:
        player_list.append(a_tag.text)  # Get player name
        playerURL_list.append(a_tag['href'])  # Get player URL

# Output the results
player_names = [name for name in player_list if name not in ['PHI', 'BAL', 'DET', 'ATL', 'CIN', 'GNB', 'IND', 'MIN', 'TAM', 'ARI', 'MIA', 'NOR', 'LAR', 'NYJ', 'CHI', 'JAX', 'DAL', 'PIT', 'HOU', 'TEN', 'SFO', 'WAS', 'NWE', 'LVR', 'KAN', 'BUF', 'DEN', 'SEA', 'LAC', 'CAR', 'AP-2', 'PB']]
#print("Player Names:", player_names)
player_urls = [i for i in playerURL_list if i.startswith('/players/')]
#print("Player URLs:", player_urls)


res2 = requests.get(rootURL + player_urls[0], headers=headers)
soup2 = BeautifulSoup(res2.text, features="html.parser")


# Find the table with rushing and receiving stats
stats_table = soup2.find('table', id='rushing_and_receiving')
#print("Found stats table:", stats_table is not None)

if stats_table:
    # Get all rows from the table
    rushing_receiving = stats_table.find_all('tr')  # Remove class filter to get all rows
    print("Number of rows found:", len(rushing_receiving))

# Initialize a list to hold DataFrames for each year
all_years_data = []

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
    'rec_td': 'TD',  # Note: This is repeated; consider renaming if needed
    'rec_first_down': '1D',  # Note: This is repeated; consider renaming if needed
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
    'awards': 'Awards'
}

# Format the data to match the headers and create a DataFrame for each year
for row in rushing_receiving:
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
final_df = pd.DataFrame(all_years_data)

# Drop rows where all columns are NA
final_df = final_df.dropna(how='all')

# Filter out summary rows by requiring Age, Team, or Lg to have a value
final_df = final_df[final_df[['Age', 'Team', 'Lg']].notna().any(axis=1)]


print(final_df)








    