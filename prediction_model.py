import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
import csv

# Read the CSV files
train_data = pd.read_csv('train.csv')
test_data = pd.read_csv('test.csv')

features = ['G', 'GS', 'Att', 'Yds', 'TD', '1D', 'Succ%', 'Lng', 'Y/A', 'Y/G', 'A/G', 'Tgt', 'Rec', 'Y/R', 'R/G', 'Ctch%', 'Y/Tgt', 'Touch', 'Y/Tch', 'YScm', 'RRTD', 'Fmb', 'FP']

# We are predicting "current" season touchdowns 
target = 'FP' 


# initialize the linear regression
model = LinearRegression()

# Create an imputer that will replace NaN with the mean value of each column
imputer = SimpleImputer(strategy='mean')

# Fit and transform the training data
X_train = imputer.fit_transform(train_data[features])
X_test = imputer.transform(test_data[features])

# Now use the imputed data for fitting and prediction
model.fit(X_train, train_data[target])
preds = model.predict(X_test)

# don't forget to set an index so your 
# predictions match the correct rows
preds = pd.Series(preds, index=test_data.index)
print(preds)

# Use player names and predictions when writing results
with open('flex.csv', mode='w') as flex:
    writer = csv.writer(flex, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    writer.writerow(['Player', 'Predicted_FP'])  # Add header row
    for i, pred in enumerate(preds):
        player_name = test_data.iloc[i]['Player']  # Assuming 'Player' is the column name
        writer.writerow([player_name, round(pred, 2)])  # Round prediction to 2 decimal places
