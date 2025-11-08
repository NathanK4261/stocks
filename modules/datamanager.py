'''
# datamanager

Module that manages the database for stock data, and stores news imformation on each company
'''

import sqlite3

from .errors import error_message

from pandas import read_sql_query, DataFrame

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

	def new_table(self):
		'''
		Creates a band new `stockdata` table formatted to work with other code
		'''

		# If a table for our stock data doesn't exist, create it now
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS stockdata (
				id INTEGER PRIMARY KEY,
				date TEXT,
				ticker TEXT,
				industry TEXT,
				sector TEXT,
				previousClose DOUBLE,
				regularMarketPrice DOUBLE,
				open DOUBLE,
				dayLow DOUBLE,
				dayHigh DOUBLE,
				beta DOUBLE,
				trailingPE DOUBLE,
				forwardPE DOUBLE,
				volume DOUBLE,
				averageVolume DOUBLE,
				averageVolume10days DOUBLE,
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
				news BLOB,
				sentiment DOUBLE,
				UNIQUE(id, date, ticker)
			)
		''')

		self.conn.commit()

	def add_data(self, data: dict):
		'''
		Adds data for a specific ticker to the `stockdata` table
		'''

		if len(data) != 36:
			# Had to delcrate as "str" for documenation reasons
			return str(error_message('datamanager.py', f'36 data points are required, {len(data)} {'were' if len(data) == 1 else 'was'} given', ValueError))

		try:	
			#Add values to dataframe

			columns = ', '.join(data.keys())
			placeholders = ', '.join(['?'] * len(data))
			values = list(data.values())

			self.cursor.execute(
				f'INSERT INTO stockdata ({columns}) VALUES ({placeholders})',
				values
			)

			self.conn.commit()

		except sqlite3.IntegrityError as e:
			if 'UNIQUE' in str(e):
				return str(error_message('datamanager.py', 'Data already exists for given date', e))
		except sqlite3.OperationalError as e:
			return str(error_message('datamanager.py', 'Error while adding stock data to database', e))
		
	def data_exists(self, date: str, ticker: str):
		'''
		Checks if data for a stock has been entered (for a specific day)
		'''

		# Query to check if the row exists
		return self.cursor.execute('''SELECT 1 FROM stockdata WHERE date = ? AND ticker = ? LIMIT 1''', (date, ticker)).fetchone() is not None
				
	def to_pandas(self):
		'''
		Returns the `stockdata` table as a pandas dataframe
		'''
		return read_sql_query('SELECT * FROM stockdata', self.conn)

	def commit(self):
		'''
		Saves all changes to the database
		'''

		self.conn.commit()

	def disconnect(self):
		'''
		Disconnects user from database
		'''
		self.conn.close()