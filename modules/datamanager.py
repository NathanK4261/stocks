'''
Module that manages the database for stock data, and stores news imformation on each company
'''
import pickle

from . import errors
import pandas as pd
from torch.utils.data import DataLoader
from . import ml
from . import valuations
from numpy import array
from torch import from_numpy
from sklearn.preprocessing import RobustScaler

# Do these do avoid warnings
pd.options.mode.chained_assignment = None
pd.set_option('future.no_silent_downcasting', True)

class DataManager:
	'''
	# DataManager

	Manages stock data storage
	'''
	def __init__(self):

		# Check if a saved DataFrame already exists
		try:
			self.stockdata = pd.read_csv('stockdata/stockdata.csv')
		
		# If no DataFrame exists, set self.stockdata to "None"
		except FileNotFoundError:
			self.stockdata = None
	
	def add_data(self, data: pd.DataFrame):
		'''
		Adds data for a specific ticker to the `stockdata` dataframe
		'''
		if self.stockdata is None:
			self.stockdata = data
		
		self.stockdata = pd.concat([self.stockdata, data])
	
	def data_exists(self, date: str, ticker: str):
		'''
		Checks if data for a stock has been entered (for a specific day)
		'''
		return not self.stockdata.loc[(self.stockdata['date'] == date) & (self.stockdata['ticker'] == ticker)].empty
	
	def save(self):
		'''
		Saves the DataFrame to file
		'''
		self.stockdata.to_csv('stockdata/stockdata.csv')

class StockDataManager:
	'''
	# StockDataManager

	Class that manages the data used to train `StockNet`
	'''

	def __init__(self):
		# Try and load our stockdata from file
		try:
			self.stockdata = pd.read_csv('stockdata/stockdata.csv')
		except FileNotFoundError as e:
			raise errors.error('datamanager.py','Couldn\'t find stockdata in file', e)

	def train_test_split(self, LSTM_window_size: int, batch_size, split_size: int = 0.6):
		'''
		Uses `sklearn.preprocessing.StandardScaler` to standardize stock data

		:param LSTM_window_size: The size of the "window" **in days**. A size of 3 would equal 3 days long

		:param batch_size: The batch size the dataloaders will use, defaults to 8
		:type batch_size: int

		:param split_size: What % of the data will be in the **train** dataset, defaults to 0.6 (60%)
		:type split_size: int
		'''
		# Use default stock data
		stockdata = self.stockdata

		# Drop unnecessary columns (do this here so if the stock data is custom, there isn't any error when dropping columns)
		stockdata = stockdata.drop(['id', 'industry', 'sector', 'date', 'news'], axis=1)

		# For each ticker, format its data
		stockdata_formatted = []
		for ticker in stockdata['ticker'].unique():

			# Pull data for specific ticker
			df = stockdata.loc[stockdata['ticker'] == ticker].copy()

			# Skip companies with insufficient data
			if len(df) <= LSTM_window_size:
				continue

			# Add "expectedReturn" column that stores the percent return for the next day (this is what we are trying to predict)
			df['expectedReturn'] = (df['regularMarketPrice'].shift(-1) - df['regularMarketPrice']) / df['regularMarketPrice']

			# Process numeric columns individually
			for col in df.columns:

				# Skip columns that are not numbers
				if col in ['ticker', 'expectedReturn']:
					continue

				# Fix missing data
				df[col] = df[col].interpolate(method='linear')
				df[col] = df[col].ffill()
				df[col] = df[col].fillna(0)

			# Append formatted data, removing the last row as it is not usefull
			stockdata_formatted.append(df.drop(df.tail(1).index))

		# Iterate through each company, and format data into sequences
		X, y = [], []
		for company_data in stockdata_formatted:

			# Seperate data into input and output (also seperate input into numeric and categorial)
			inp = company_data.drop(['ticker', 'expectedReturn'], axis=1).astype('float32').reset_index(drop=True)
			out = company_data['expectedReturn'].astype('float32').reset_index(drop=True)

			# Create sequences of 2-day periods
			for i in range(len(inp) - LSTM_window_size + 1):

				# Add data to "X" and "y" lists
				X.append( inp.iloc[i : (i + LSTM_window_size)] )
				y.append([ out.iloc[ i + LSTM_window_size-1 ] ]) # Add "[]" to make the output array 2D

		# Convert y into a numpy array
		y = array(y)

		# Split into train/test sets
		split_idx = int(len(X) * split_size)

		X_train, X_test = X[:split_idx], X[split_idx:]
		y_train, y_test = y[:split_idx], y[split_idx:]

		# Transform with StandardScaler
		scaler = StandardScaler()
		
		# Fit scaler on training data ONLY. Make sure to concatenate to remove sequences for fitting
		scaler.fit(pd.concat(X_train, ignore_index=True))

		# Transform X_train and X_test using the scaler, this will convert our list of dataframes to a list of numpy arrays
		X_train = [scaler.transform(df) for df in X_train]
		X_test = [scaler.transform(df) for df in X_test]

		# Save our scaler for inference later on
		with open('StockNet/scaler', 'wb') as f:
			pickle.dump(scaler, f)

		# Now, convert our training and testing data into dataloaders for model training
		train_dataloader = DataLoader(
			StockNetDataset(
				from_numpy(array(X_train)),
				from_numpy(y_train)
			),
			batch_size=batch_size,
			shuffle=True
		)

		test_dataloader = DataLoader(
			StockNetDataset(
				from_numpy(array(X_test)),
				from_numpy(y_test)
			),
			batch_size=batch_size,
			shuffle=False # We want validation to be the same for each epoch
		)

		# Return the train/test split
		return train_dataloader, test_dataloader
	
	def get_ticker_data(self, ticker: str):
		'''
		Returns a formatted dataframe of the stock data for a particular ticker

		:param ticker: The company's ticker symbol
		:type ticker: str
		'''
		# Use default stock data
		stockdata = self.stockdata

		# Drop unnecessary columns (do this here so if the stock data is custom, there isn't any error when dropping columns)
		stockdata = stockdata.drop(['id', 'industry', 'sector', 'news'], axis=1)

		# For each ticker, format its data
		stockdata_formatted = []

		# Pull data for specific ticker
		df = stockdata.loc[stockdata['ticker'] == ticker].copy()

		# Get the dates
		dates = df['date']

		# Drop more columns
		df = df.drop(['date'], axis=1)
		df = df.drop(['ticker'], axis=1)

		# Process numeric columns individually
		for col in df.columns:

			# Fix missing data
			df[col] = df[col].interpolate(method='linear')
			df[col] = df[col].ffill()
			df[col] = df[col].fillna(0)

		# Append formatted data, removing the last row as it is not usefull
		stockdata_formatted.append(df.drop(df.tail(1).index))

		# Concatenate formatted stock data
		stockdata_formatted_concat = pd.concat(stockdata_formatted)
		
		# Load scaler from our training data
		with open('StockNet/scaler', 'rb') as f:
			scaler = pickle.load(f)

		# Fit scaler on stock data
		stockdata_formatted_scaled = pd.DataFrame(
			scaler.transform(stockdata_formatted_concat),
			columns=stockdata_formatted_concat.columns,
			index=stockdata_formatted_concat.index
		)

		# Return scaled data
		return dates, stockdata_formatted_scaled