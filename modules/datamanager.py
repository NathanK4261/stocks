'''
# datamanager

Module that manages the database for stock data, and stores news imformation on each company
'''

import sqlite3

from .errors import error_message

class DatabaseManager:
	'''
	# DatabaseManager

	Manages actions within the "stockdata" database
	'''
	def __init__(self):

		# Connect to the database
		self.conn = sqlite3.connect('stockdata/stockdata.db')

		# Set up the cursor
		self.cursor = self.conn.cursor()

		# If a table for our stock data doesn't exist, create it now
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS stockdata (
				ticker TEXT,
				date TEXT,
				industry TEXT,
				sector TEXT,
				previousClose DOUBLE,
				currentPrice DOUBLE,
				open DOUBLE,
				dayLow DOUBLE,
				dayHigh DOUBLE,
				beta DOUBLE,
				trailingPE DOUBLE,
				forwardPE DOUBLE,
				volume DOUBLE,
				averageVolume DOUBLE,
				averageVolume10days DOUBLE,
				bid DOUBLE,
				ask DOUBLE,
				marketCap DOUBLE,
				fiftyTwoWeekLow DOUBLE,
				fiftyTwoWeekHigh DOUBLE,
				priceToSalesTrailing12Months DOUBLE,
				fiftyDayAverage DOUBLE,
				twoHundredDayAverage DOUBLE,
				profitMargins DOUBLE,
				shortRatio DOUBLE,
				bookValue DOUBLE,
				priceToBook DOUBLE,
				earningsQuarterlyGrowth DOUBLE,
				epsTrailingTwelveMonths DOUBLE,
				epsForward DOUBLE,
				enterpriseToRevenue DOUBLE,
				quickRatio DOUBLE,
				currentRatio DOUBLE,
				returnOnAssets DOUBLE,
				returnOnEquity DOUBLE,
				trailingPegRatio DOUBLE,
				sentiment DOUBLE,
				UNIQUE(ticker, date)
			)
		''')

		self.commit_all()

	def add_data(self, data: dict):
		'''
		Adds data for a specific ticker to the database
		'''

		if len(data) != 37:
			# Had to delcrate as "str" for documenation reasons
			return str(error_message('datamanager.py', f'37 data points are required, {len(data)} {'were' if len(data) == 1 else 'was'} given'))

		try:
			# Iterate through the data stored in the dict
			for datapoint in data:
				
				# Individually add each value to make sure they are assigned to correct columns
				if type(datapoint) == str:
					self.cursor.execute(f'INSERT INTO stockdata ({datapoint}) VALUES ("{data[datapoint]}")')
				else:
					self.cursor.execute(f'INSERT INTO stockdata ({datapoint}) VALUES ({data[datapoint]})')

		except sqlite3.IntegrityError as e:
			if 'UNIQUE' in str(e):
				return str(error_message('database.py', 'Data already exists for given date', e))
		except sqlite3.OperationalError as e:
			return str(error_message('database.py', 'Error while adding stock data to database', e))
		
	def commit_all(self):
		'''
		Saves all changes to the database
		'''

		self.conn.commit()

	def disconnect(self):
		'''
		Disconnects user from database
		'''
		self.conn.close()