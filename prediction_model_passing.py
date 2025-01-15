import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import csv

# Load data
train_data = pd.read_csv("data_used/train2.csv")
test_data = pd.read_csv("data_used/test2.csv")

# Strip whitespace from column names
train_data.columns = train_data.columns.str.strip()
test_data.columns = test_data.columns.str.strip()


# Prepare training data
features = ['Age', 'G', 'GS', 'Cmp', 'Att', 'Cmp%', 'Yds', 'TD', 'Int', 'Y/A', 'Rate']
X = np.array(train_data[features])  # No need to exclude 'Player' since it's not in features
y = np.array(train_data['FP'])

# Initialize imputer
imputer = SimpleImputer(strategy='mean')

# Train model using LassoCV
model = LassoCV(cv=5, random_state=42, max_iter=2000)
X = imputer.fit_transform(X)
model.fit(X, y)

# Prepare test data
X_test = imputer.transform(np.array(test_data[features]))  # Use the same features for test data

# Make predictions
test_predictions = model.predict(X_test)

# Add predictions to the test dataset
test_data['Predicted_FP'] = test_predictions



df = pd.read_csv('data_used/train.csv')
if (test_data['Pos'] == 'QB').any():
    if test_data['Player'].isin(df['Player']).any():
        #addthe fp in the train dataset which is rushing data to test_data fp which is passing data
        test_data['Predicted_FP'] = test_data['Predicted_FP'] + df['FP']

predictions_df = test_data[test_data['Pos'] == 'QB'][['Player', 'Predicted_FP']]


# Function to calculate injury risk factor based on games played
def calculate_injury_risk_factor(player_name):
    # Normalize player name for comparison
    normalized_player_name = player_name.strip().lower()
    
    # Debug: Print the normalized player name
    print(f"Calculating injury risk for: {normalized_player_name}")
    
    player_history = train_data[train_data['Player'].str.strip().str.lower() == normalized_player_name]
    
    if player_history.empty:
        print(f"No history found for player: {normalized_player_name}, returning default risk factor of 1.0")
        return 1.0
    
    # Use the 'G' column to determine games played
    games_played = player_history['G'].iloc[-1] if 'G' in player_history.columns else 1
    
    # Get the player's age
    player_age = player_history['Age'].iloc[-1] if 'Age' in player_history.columns else 0
    
    # Calculate regression factor based on age
    regression_factor = 1.0 - (0.1 * (player_age / 30))  # Increased impact of age on performance decline
    
    # Calculate injury risk factor based on games played
    injury_risk_factor = max(1.0 - (0.15 * (17 - games_played) / 17), 0.1)  # Increased scaling factor
    print(injury_risk_factor)
    
    overall_risk_factor = injury_risk_factor * regression_factor
    
    # Debug: Print calculated values
    print(f"Player: {player_name}, Games Played: {games_played}, Age: {player_age}, Injury Risk Factor: {overall_risk_factor}")
    
    return overall_risk_factor

# Make predictions with injury risk adjustment
predictions_df['Injury_Risk_Factor'] = predictions_df['Player'].apply(calculate_injury_risk_factor)

# Adjust the predicted FP by applying a scaling factor
scaling_factor = 0.85  # Adjust this value as needed
predictions_df['Predicted_FP'] = predictions_df['Predicted_FP'] * predictions_df['Injury_Risk_Factor'] * scaling_factor

# Debug: Print adjusted predictions
print("\nAdjusted Predictions:")
print(predictions_df[['Player', 'Predicted_FP', 'Injury_Risk_Factor']])

# Save predictions to CSV
with open('data_used/flex2.csv', mode='w', newline='') as flex:
    writer = csv.writer(flex)
    writer.writerow(['Player', 'Predicted_FP'])
    for _, row in predictions_df.iterrows():
        writer.writerow([row['Player'], round(row['Predicted_FP'], 1)])


coef_df = pd.DataFrame({
    'Feature': features,
    'Coefficient': model.coef_
})
print("\nFeature Coefficients:")
print(coef_df.sort_values('Coefficient', key=abs, ascending=False))
