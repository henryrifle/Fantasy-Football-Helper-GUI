import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
import xgboost as xgb

# Load data
train_data = pd.read_csv("data_used/train.csv", sep=",")
test_data = pd.read_csv("data_used/test.csv", sep=",")

# Feature engineering - add interaction terms and normalized features
def create_advanced_features(df):
    df_new = df.copy()
    # Yards per attempt
    df_new['YPA'] = df_new['Yds'] / df_new['Att'].replace(0, 1)
    # Yards per target
    df_new['YPT'] = df_new['Yds'] / df_new['Tgt'].replace(0, 1)
    # TD rate
    df_new['TD_Rate'] = df_new['TD'] / df_new['Att'].replace(0, 1)
    # Usage rate
    df_new['Usage'] = (df_new['Att'] + df_new['Tgt']) / df_new['G'].replace(0, 1)
    return df_new

# Create advanced features for both datasets
train_data = create_advanced_features(train_data)
test_data = create_advanced_features(test_data)

# Update features list with new features
features = [
    'G', 'GS', 'Att', 'Yds', 'TD',          
    'Rec', 'YScm', 'RRTD', 'Touch',         
    'Tgt', 'Y/R', 'YPA', 'YPT', 'TD_Rate', 'Usage'                            
]

# Prepare historical data
X_historical = np.array(train_data[features])
y_historical = np.array(train_data['FP'])

# Prepare recent data
X_recent = np.array(test_data[features])
y_recent = np.array(test_data['FP'])

# Initialize imputer with median strategy instead of mean
imputer = SimpleImputer(strategy='median')
X_historical = imputer.fit_transform(X_historical)
X_recent = imputer.transform(X_recent)

# Normalize features to improve model stability
scaler = StandardScaler()
X_historical = scaler.fit_transform(X_historical)
X_recent = scaler.transform(X_recent)

# Adjust weights for a more balanced approach
weight_recent = 0.6
weight_historical = 0.4

X_combined = np.vstack([
    X_historical * weight_historical,
    X_recent * weight_recent
])
y_combined = np.concatenate([y_historical, y_recent])

# Update XGBoost parameters to be more conservative
xgb_model = XGBRegressor(
    n_estimators=300,          # More trees for stability
    learning_rate=0.01,        # Much lower learning rate
    max_depth=3,               # Reduced depth to prevent overfitting
    min_child_weight=5,        # Increased to prevent overfitting
    subsample=0.7,             # Reduced to prevent overfitting
    colsample_bytree=0.7,      # Reduced to prevent overfitting
    gamma=2,                   # Increased minimum loss reduction
    reg_alpha=0.5,            # Increased L1 regularization
    reg_lambda=2,             # Increased L2 regularization
    random_state=42
)

# Use KFold instead of default CV for more stable results
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(xgb_model, X_combined, y_combined, cv=kf, scoring='r2')

# Calculate and print CV scores
print("\nCross-validation R² scores:", cv_scores)
print("Average CV R² score: %0.3f (+/- %0.3f)" % (cv_scores.mean(), cv_scores.std() * 2))

# Create evaluation set
eval_set = [(X_combined, y_combined)]

# Fit model with proper early stopping syntax for older XGBoost versions
xgb_model.fit(
    X_combined, 
    y_combined,
    eval_set=eval_set,
    verbose=False
)

# Scale test data before prediction
X_test = scaler.transform(np.array(test_data[features]))
predictions = xgb_model.predict(X_test)

# Clip predictions to reasonable range (e.g., 0 to 400 fantasy points)
predictions = np.clip(predictions, 0, 400)

# Create predictions DataFrame
predictions_df = pd.DataFrame({
    'Player': test_data['Player'],
    'Predicted_FP': predictions
})

# Check for duplicates and keep only first occurrence
duplicate_players = predictions_df['Player'].duplicated(keep='first')
if duplicate_players.any():
    print("\nRemoving duplicate entries for players:")
    print(predictions_df[duplicate_players]['Player'].unique())
    predictions_df = predictions_df[~predictions_df['Player'].duplicated(keep='first')]

# Feature importance
importance_df = pd.DataFrame({
    'Feature': features,
    'Importance': xgb_model.feature_importances_
})

# Save skilled position predictions to flex.csv
predictions_df[['Player', 'Predicted_FP']].to_csv('data_used/flex.csv', index=False)

print("\nFeature Importance:")
print(importance_df.sort_values(by='Importance', ascending=False))

print("\nPredictions:")
print(predictions_df)

