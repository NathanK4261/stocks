'''
Takes data from the `stockdata` table and formats it into a pickled pandas dataframe, which will be used to train StockNet
'''

from modules.datamanager import DatabaseManager

from sklearn.preprocessing import StandardScaler

import pandas as pd
pd.options.mode.chained_assignment = None
pd.set_option('future.no_silent_downcasting', True)

# StandardScaler
scaler = None

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

	# Insert data into the "descision" column
	df['investmentDecision'] = (df['regularMarketPrice'] < df['regularMarketPrice'].shift(-1)).astype(int)

	# Process numeric columns individually
	for col in df.columns:

		# Skip label column
		if col == 'investmentDecision' or col == 'ticker':
			continue

		# Fix missing data
		df[col] = df[col].interpolate(method='linear')
		df[col] = df[col].ffill()
		df[col] = df[col].fillna(0)

	# Re-initialize scaler
	scaler = StandardScaler()

	# Remove columns that do not need to be standardized
	df_scaler = df.drop(['ticker', 'investmentDecision'], axis=1)

	# Standardize data
	df_transformed = scaler.fit_transform(df_scaler)

	# Turn numpy array from scaler back into pandas dataframe
	df_processed = pd.DataFrame(data=df_transformed, index=df_scaler.index, columns=df_scaler.columns)

	# Copy data back into df
	df.update(df_processed)

	# Move the formatted data back into the main dataframe
	stockdata.loc[stockdata['ticker'] == ticker, :] = df

# Save as CSV
stockdata.to_csv('stockdata/training_data.csv', index=False)