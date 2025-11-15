'''
Module that allows for inference with the `StockNet` model
'''

from . import ml
import pandas as pd
from numpy import array
import sqlite3

from sklearn.preprocessing import StandardScaler

class Inference:
	def __init__(self, database_path: str, model_path: str, device: str):
		'''
		:param self:
		:param database_path: stockdata/stockdata.db
		:type database_path: str
		:param model_path:
		:type model_path: str
		:param device: mps, cuda, or cpu
		:type device: str
		'''
		# Get stock data
		conn = sqlite3.connect(database_path)
		self.stockdata = pd.read_sql_query('SELECT * FROM stockdata', conn)
		conn.close()

		# Initialize scaler
		self.scaler = StandardScaler()

		# Load StockNet
		try:
			# Try and load a previous version
			self.model = ml.StockNet().to(device)
			self.model.load_state_dict(ml.torch.load(model_path,weights_only=True))
		except:
			# If no model found in file, make new one
			self.model = ml.StockNet().to(device)

		self.device = device

	def predict(self, ticker: str):
		'''
		Predicts weather to buy or sell a stock, where 0 = SELL and 1 = BUY.

		Also returns the confidence of `StockNet`'s descision
		
		:param self:
		:param ticker: A string prepresenting the ticker of a company
		:type ticker: str
		'''

		# Obtain data for a specific ticker
		df = self.stockdata.loc[self.stockdata['ticker'] == ticker]

		# Remove columns not needed for prediction
		df = df.drop(['id', 'ticker', 'date', 'industry', 'sector', 'news'], axis=1)

		# Process numeric columns individually
		for col in df.select_dtypes(include=['float64']).columns:

			# Skip label column
			if col == 'investmentDecision':
				continue

			# Fix missing data
			df[col] = df[col].interpolate(method='linear')
			df[col] = df[col].ffill()
			df[col] = df[col].fillna(0)

			# Scale this specific column with its own scaler
			scaler = StandardScaler()
			df[col] = scaler.fit_transform(df[[col]])

		# Get the last 2 days worth of data
		inputs = []
		inputs.append(df.iloc[-2:])
		
		# Convery to numpy, then torch tensor
		inputs = array(inputs, dtype='float32')
		inputs = ml.torch.from_numpy(inputs).to(self.device)

		# Set the model to evaluation mode, disabling dropout and using population
		# statistics for batch normalization.
		self.model.eval()

		# Disable gradient computation and reduce memory consumption.
		with ml.torch.no_grad():
			output, _, _ = self.model(inputs)

			# Since we are doing prediction, run a sigmoid function to get a value between 0 and 1
			pred = ml.torch.sigmoid(output)

			# Get the confidence of the prediction
			conf = int(pred*100)
		
		# Return prediction and confidence
		return pred, conf
	
	def predict_many(self, tickers: list):
		'''
		Returns a ranked `DataFrame` on the best investments for tommorow (according to `StockNet`)
		
		:param self:
		:param tickers: List of string objects prepresenting stock tickers
		:type tickers: list
		'''
		data = []

		# Set the model to evaluation mode, disabling dropout and using population
		# statistics for batch normalization.
		self.model.eval()

		# Disable gradient computation and reduce memory consumption.
		with ml.torch.no_grad():
			for ticker in tickers:
				# Obtain data for a specific ticker
				df = self.stockdata.loc[self.stockdata['ticker'] == ticker]

				# Remove columns not needed for prediction
				df = df.drop(['id', 'ticker', 'date', 'industry', 'sector', 'news'], axis=1)

				# Process numeric columns individually
				for col in df.select_dtypes(include=['float64']).columns:

					# Skip label column
					if col == 'investmentDecision':
						continue

					# Fix missing data
					df[col] = df[col].interpolate(method='linear')
					df[col] = df[col].ffill()
					df[col] = df[col].fillna(0)

					# Scale this specific column with its own scaler
					scaler = StandardScaler()
					df[col] = scaler.fit_transform(df[[col]])

				# Get the last 2 days worth of data
				inputs = []
				inputs.append(df.iloc[-2:])
				
				# Convery to numpy, then torch tensor
				inputs = array(inputs, dtype='float32')
				inputs = ml.torch.from_numpy(inputs).to(self.device)

				# Run a prediction on the company stock
				output, _, _ = self.model(inputs)

				# Since we are doing prediction, run a sigmoid function to get a value between 0 and 1
				pred = ml.torch.sigmoid(output)

				# Get the confidence of the prediction
				conf = int(pred.item()*100)

				# Append a tuple of our results
				data.append((ticker, pred.item(), conf))

		# Create DataFrame from our results
		rankings = pd.DataFrame(data, columns=['TICKER', 'PREDICTION', 'CONFIDENCE'])

		# Sort in order of highest to olwest confidence
		rankings = rankings.sort_values(by=['CONFIDENCE'], ascending=False)

		return rankings