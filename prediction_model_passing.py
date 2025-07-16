import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, KFold
import csv

# Load data
train_data = pd.read_csv("data_used/train2.csv")
test_data = pd.read_csv("data_used/test2.csv")

# Strip whitespace from column names
train_data.columns = train_data.columns.str.strip()
test_data.columns = test_data.columns.str.strip()

def create_advanced_features(df):
    df_new = df.copy()
    # Passing efficiency metrics
    df_new['TD_Rate'] = df_new['TD'] / df_new['Att'].replace(0, 1)
    df_new['Int_Rate'] = df_new['Int'] / df_new['Att'].replace(0, 1)
    df_new['Comp_Rate'] = df_new['Cmp'] / df_new['Att'].replace(0, 1)
    df_new['YPA'] = df_new['Yds'] / df_new['Att'].replace(0, 1)
    df_new['Points_Per_Game'] = df_new['FP'] / df_new['G'].replace(0, 1)
    df_new['TD_Per_Game'] = df_new['TD'] / df_new['G'].replace(0, 1)
    return df_new

# Create advanced features
train_data = create_advanced_features(train_data)
test_data = create_advanced_features(test_data)

# Features for QB prediction
features = [
    'Age', 'G', 'GS', 'Cmp', 'Att', 'Cmp%', 
    'Yds', 'TD', 'Int', 'Y/A', 'Rate',
    'TD_Rate', 'Int_Rate', 'Comp_Rate', 'YPA',
    'Points_Per_Game', 'TD_Per_Game'
]

# Prepare data
X_historical = np.array(train_data[features])
y_historical = np.array(train_data['FP'])

X_recent = np.array(test_data[features])
y_recent = np.array(test_data['FP'])

# Initialize imputer and scaler
imputer = SimpleImputer(strategy='median')
scaler = StandardScaler()

# Transform data
X_historical = imputer.fit_transform(X_historical)
X_recent = imputer.transform(X_recent)

X_historical = scaler.fit_transform(X_historical)
X_recent = scaler.transform(X_recent)

# Combine data with weights
weight_recent = 0.65
weight_historical = 0.35

X_combined = np.vstack([
    X_historical * weight_historical,
    X_recent * weight_recent
])
y_combined = np.concatenate([y_historical, y_recent])

# Update XGBoost parameters to prevent ceiling effect
xgb_model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.01,        # Reduced learning rate
    max_depth=3,               # Reduced depth
    min_child_weight=5,        # Increased to prevent overfitting
    subsample=0.7,             # Reduced to prevent overfitting
    colsample_bytree=0.7,      # Reduced to prevent overfitting
    gamma=1,                   # Increased minimum loss reduction
    reg_alpha=0.5,            # Increased L1 regularization
    reg_lambda=2,             # Increased L2 regularization
    random_state=42
)

# Calculate and print CV scores
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(xgb_model, X_combined, y_combined, cv=kf, scoring='r2')
print("\nCross-validation R² scores:", cv_scores)
print("Average CV R² score: %0.3f (+/- %0.3f)" % (cv_scores.mean(), cv_scores.std() * 2))

# Fit model
xgb_model.fit(X_combined, y_combined)

# Make predictions
X_test = scaler.transform(np.array(test_data[features]))

# Adjust clipping range to be more realistic for QB scoring
max_fp = train_data['FP'].max() * 1.1  # Allow 10% above historical maximum
predictions = xgb_model.predict(X_test)
predictions = np.clip(predictions, 0, max_fp)

# Create predictions dataframe with more detail
predictions_df = pd.DataFrame({
    'Player': test_data['Player'],
    'Predicted_FP': predictions,
})

# Sort by predicted fantasy points
predictions_df = predictions_df.sort_values('Predicted_FP', ascending=False)

# Print feature importance
importance_df = pd.DataFrame({
    'Feature': features,
    'Importance': xgb_model.feature_importances_
})

# Save QB predictions to flex2.csv
predictions_df[['Player', 'Predicted_FP']].to_csv('data_used/flex2.csv', index=False)

print("\nFeature Importance:")
print(importance_df.sort_values(by='Importance', ascending=False))

print("\nPredictions:")
print(predictions_df)
