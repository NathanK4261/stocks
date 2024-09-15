import tiingo

import pandas as pd

import requests
from bs4 import BeautifulSoup
import yfinance as yf

import json
import os

from datetime import date, datetime, timezone

class TiingoClient:
	'''
	# TiingoClient
	Uses the Tiingo.com® API to get market data for a stock trading AI
	'''
	def __init__(self):
		with open('config.json') as f:
			config = json.load(f)

		self.ticker = config['TICKER']
		self.tiingo_key = config['TIINGO_KEY']

		self.client = tiingo.TiingoClient({'session':True,'api_key':self.tiingo_key})

	def get_historical_data(self, save=True):
		'''
		Return historical data from a specific stock
		'''

		headers = {
			'Content-Type': 'application/json',
			'Authorization' : f'Token {self.tiingo_key}'
		}

		# Collect price data
		data_ohlcv = self.client.get_ticker_price(self.ticker,
			fmt='csv',
			startDate='2000-01-01',
			frequency='daily')
		
		# Collect valuation data
		data_pe_pb = self.client.get_fundamentals_daily(self.ticker,
			fmt='csv',
			startDate='2000-01-01')

		# Save the collected price data to a CSV file
		with open(f'{self.ticker}-OHLCV.csv', 'w') as f:
			for data in data_ohlcv:
				lines = data
				for line in lines:
					f.write(line)
	
		# Save the collected data to a CSV file
		with open(f'{self.ticker}-PEPB.csv', 'w') as f:
			for data in data_pe_pb:
				lines = data
				for line in lines:
					f.write(line)

		# Open the CSV files as pandas dataframes
		data_ohlcv = pd.read_csv(f'{self.ticker}-OHLCV.csv')
		data_pe_pb = pd.read_csv(f'{self.ticker}-PEPB.csv')

		# Delete the CSV files if the user wants to
		if save:
			try:
				os.remove(f'{self.ticker}-OHLCV.csv')
				os.remove(f'{self.ticker}-PEPB.csv')
			except OSError:
				pass
		else:
			# Return the pandas dataframes
			return data_ohlcv, data_pe_pb


	def get_daily_market_data(self):
		'''
		Gets specific data for a stock after the end of a market day
		'''
		headers = {
			'Content-Type': 'application/json',
			'Authorization' : f'Token {self.tiingo_key}'
		}

		# Get daily market data
		data_ohlcv = self.client.get_ticker_price(self.ticker,
			fmt='csv',
			startDate=str(date.today()),
			frequency='daily')
		
		data_pe_pb = self.client.get_fundamentals_daily(self.ticker,
			fmt='csv',
			startDate=str(date.today()))
	
		# Save the collected data to a CSV file
		with open(f'{self.ticker}-PEPB-{date.today()}.csv', 'w') as f:
			# Data goes in order: [date, close, high, low, open, volume]
			for data in data_pe_pb:
				for line in data:
					f.write(line)

		with open(f'{self.ticker}-OHLCV-{date.today()}.csv', 'w') as f:
			# Data goes in order: [date, close, high, low, open, volume]
			for data in data_ohlcv:
				for line in data:
					f.write(line)

		# Open the CSV files as pandas dataframes
		daily_data_ohlcv = pd.read_csv(f'{self.ticker}-OHLCV-{date.today()}.csv')
		daily_data_pe_pb = pd.read_csv(f'{self.ticker}-PEPB-{date.today()}.csv')

		# Delete the CSV files
		try:
			os.remove(f'{self.ticker}-OHLCV-{date.today()}.csv')
			os.remove(f'{self.ticker}-PEPB-{date.today()}.csv')
		except OSError:
			pass

		# Combine the two dataframes
		try:
			df = pd.merge(daily_data_ohlcv, daily_data_pe_pb, on='date')
		except KeyError:
			return None

		# Convert the given dates to python "datetime" objects
		df['date'] = pd.to_datetime(df['date'],utc=True).dt.date

		# Remove values that are not important
		df = df.drop(['marketCap','adjClose','adjHigh','adjLow','adjOpen','adjVolume','divCash','splitFactor'],
			axis=1
		)

		# Return the pandas dataframes
		return df

class NewsWebScraper:
	'''
	# WebScaper

	Class used to get the content of news webpages provided by `yfinance`
	'''
	def __init__(self):
		# Load config
		with open('config.json') as f:
			config = json.load(f)

		# Store the yfinance ticker object
		self.yf_ticker = yf.Ticker(config['TICKER'])

	def scrape_from_yf(self):
		'''
		Scrapes websites provided by `yfinance` and returns a list of 
		`NewsWebPage` objects
		'''

		# Make a list to store each scraped site
		scraped_sites = []

		# User-Agent headers
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
		}

		# Fetch historical news
		news_data = self.yf_ticker.get_news()

		# Get the html content of each webpage
		for news in news_data:
			# Fetch the website data
			news_content = requests.get(news['link'],
				allow_redirects=True,
				headers=headers
			)

			if news_content.status_code != 200:
				return None
			
			# Get the HTML content
			news_content = news_content.text

			# Parse the HTML content
			soup = BeautifulSoup(news_content, 'html.parser')

			# Extract class "caas-body" from "<div>"
			news_content = soup.find('div', class_='caas-body').text
			
			scraped_sites.append(
				NewsWebPage(
					news['title'],
					news['publisher'],
					news['providerPublishTime'],
					news_content,
					news['link']
				)
			)

			# Return the scraped sites as "NewsWebPage" object
			return scraped_sites

class NewsWebPage:
		'''
		# NewsWebPage

		Class used to store data about different news web pages

		NOTE: This class is used in `NewsWebScraper`, so there is no need to 
		contruct objects using this class manually
		'''
		def __init__(self, title: str, publisher: str, date: str, content: str, link: str):
			self.title = title # Title of the news article

			self.publisher = publisher # Publisher of the news article

			self.date = datetime.fromtimestamp(date, tz=timezone.utc)

			self.content = content # The content in the news article

			self.link = link

class OllamaAPI:
	'''
	# OllamaAPI
	Class used to talk to the provided Ollama API endpoint

	NOTE: This endpoint is not secured unless done so by an outside party, do not 
	share sensitive information unless you are sure nobody can access it!
	'''
	def __init__(self, server_hostname:str, ollama_model:str):
		self.url = f"http://{server_hostname}:11434/api/generate" # API Endpoint to Ollama

		self.model = ollama_model

		self.headers={
			"Content-Type":"application/json"
		}

	def send_message(self, message:str):
		'''
		Sends a message to the Ollama API
		'''

		# Create our POST data
		data = {
			"model":self.model,
			"prompt":message,
			"stream":False
		}

		# Post our response to the Ollama API
		response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

		# Return our data, or a status code indicating the error
		if response.status_code == 200:
			response = response.text
			response = json.loads(response)
			return str(response['response'])
		else:
			return response.status_code