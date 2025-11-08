'''
Takes data from the `stockdata` table and formats it into a pickled pandas dataframe, which will be used to train StockNet
'''

from modules.datamanager import DatabaseManager

from sklearn.preprocessing import StandardScaler

import pandas as pd
pd.options.mode.chained_assignment = None
pd.set_option('future.no_silent_downcasting', True)

# Initialize scaler
scaler = StandardScaler()

# Load "stockdata" table into pandas dataframe
db_man = DatabaseManager()
stockdata = db_man.to_pandas()
db_man.disconnect()

# Remove columns not needed for training neural network
stockdata = stockdata.drop(['id', 'date', 'industry', 'sector', 'news'], axis=1)

# Add "descision" column that stores weather to buy (1) or sell (0)
stockdata['investmentDecision'] = None

# Identify the different tickers in the stock data
tickers = stockdata['ticker'].unique()

# For each ticker, format its data, cleaning up missing values
for ticker in tickers:

	# Pull data for specific ticker
	df = stockdata.loc[stockdata['ticker'] == ticker]

	# Forward fill data if none exists (use last data point)
	df = df.ffill()

	# Zero fill data (if no data exists)
	df = df.fillna(0)

	for col in df:

		# Insert data into the "descision" column
		df['investmentDecision'] = (df['regularMarketPrice'] > df['previousClose']).astype(int)
		
		# Interpolate data
		if df[col].dtype == 'float64':
			df[col] = df[col].interpolate(method='linear')

			# Normalize data using scaler
			df[col] = scaler.fit_transform(df[[col]])

	# Move the formatted data back into the main dataframe
	stockdata.loc[stockdata['ticker'] == ticker, :] = df

# Save as CSV
stockdata.to_csv('stockdata/training_data.csv', index=False)