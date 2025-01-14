import pandas as pd
import numpy as np
from sklearn.linear_model import LassoCV
from sklearn.impute import SimpleImputer
import csv

# Load data
train_data = pd.read_csv("train.csv")
test_data = pd.read_csv("test.csv")

# Print available columns
#print("Available columns in training data:")
#print(train_data.columns.tolist())

def calculate_age_risk_factor(player_name, player_type):
    player_history = train_data[train_data['Player'] == player_name]
    
    if player_history.empty:
        return 1.0
    
    player_age = player_history['Age'].iloc[-1] if 'Age' in player_history.columns else 25
    
    # More aggressive thresholds and decay rates
    if player_type > 0.3:  # Receiver (lowered threshold to better identify RBs)
        age_threshold = 27
        decay_rate = 0.15
    else:  # RB - more aggressive decay
        age_threshold = 25
        decay_rate = 0.10  
    
    # Calculate age factor
    if player_age <= age_threshold:
        age_factor = 1.0
    else:
        age_factor = np.exp(-decay_rate * (player_age - age_threshold))
    
    # Debug print
    #print(f"Player: {player_name}, Age: {player_age}, Type: {'Receiver' if player_type > 0.3 else 'RB'}, Factor: {age_factor:.3f}")
    
    return age_factor

# Calculate receiving vs rushing ratio to determine player type
def calculate_player_type_factor(row):
    total_yards = row['Yds'] if row['Yds'] > 0 else 1
    total_touches = row['Touch'] if row['Touch'] > 0 else 1
    
    # Calculate receiving ratio based on receptions vs total touches
    rec_ratio = row['Rec'] / total_touches if total_touches > 0 else 0
    
    # Debug print
    #print(f"Player: {row['Player']}, Rec Ratio: {rec_ratio:.3f}")
    
    return rec_ratio

# Keep all features but add interaction terms
features = [
    'G', 'GS', 'Att', 'Yds', 'TD',          # Core stats
    'Rec', 'YScm', 'RRTD', 'Touch',         # Usage stats
    'Tgt', 'Y/R'                            # Receiving efficiency
]

# Prepare training data
X = np.array(train_data[features])
y = np.array(train_data['FP'])

# Initialize imputer
imputer = SimpleImputer(strategy='mean')

# Train model
model = LassoCV(cv=5, random_state=42, max_iter=2000)
X = imputer.fit_transform(X)
model.fit(X, y)

# Make predictions with position-aware adjustments
X_test = imputer.transform(np.array(test_data[features]))
base_predictions = model.predict(X_test)

# Calculate adjustments for each player
predictions = []
for idx, row in test_data.iterrows():
    pred = base_predictions[idx]
    
    # Calculate player type factor (0 = pure rusher, 1 = pure receiver)
    player_type = calculate_player_type_factor(row)
    
    # Adjust injury risk based on player type and age
    games_played = row['G']
    touches_per_game = row['Touch'] / games_played if games_played > 0 else 0
    
    # More forgiving injury factor for receiving-heavy players
    base_touch_penalty = 30 + (20 * player_type)
    injury_factor = np.clip(
        games_played/17 * np.exp(-touches_per_game/base_touch_penalty), 
        0.8 + (0.1 * player_type),
        1.0
    )
    
    # Add age-based risk factor
    age_factor = calculate_age_risk_factor(row['Player'], player_type)
    injury_factor = injury_factor * age_factor
    
    # Games played projection
    games_factor = np.minimum(16/max(games_played, 1), 1.3)
    
    # Apply baseline minimum based on games played
    min_fp = 50 if games_played > 8 else 0
    
    # Apply adjustments
    pred = max(pred, min_fp)
    pred = pred * injury_factor * games_factor
    
    # Universal maximum cap
    max_fp = 500  # Remove the player-type based cap
    pred = min(pred, max_fp)
    
    predictions.append(pred)

predictions = np.array(predictions)

# Before saving predictions to CSV, aggregate duplicates by taking the mean
predictions_df = pd.DataFrame({
    'Player': test_data['Player'],
    'Predicted_FP': predictions
})

# Group by Player and take the mean of predictions
predictions_df = predictions_df.groupby('Player')['Predicted_FP'].mean().reset_index()

# Save predictions to CSV
with open('data_used/flex.csv', mode='w', newline='') as flex:
    writer = csv.writer(flex)
    writer.writerow(['Player', 'Predicted_FP'])
    for _, row in predictions_df.iterrows():
        writer.writerow([row['Player'], round(row['Predicted_FP'], 1)])

# Print feature importance and statistics
coef_df = pd.DataFrame({
    'Feature': features,
    'Coefficient': model.coef_
})
print("\nFeature Coefficients:")
print(coef_df.sort_values('Coefficient', key=abs, ascending=False))

print("\nPrediction Statistics:")
print(f"Mean FP: {predictions.mean():.1f}")
print(f"Max FP: {predictions.max():.1f}")
print(f"Min FP: {predictions.min():.1f}")


