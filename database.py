from modules.internet import YahooClient, NewsWebScraper
from modules.llm import LlamaChat

import modules.tickers
from yfinance import Ticker

from datetime import datetime, date
import time
import pytz

import pandas as pd
from statistics import mean

import json
import logging

def is_market_open():
	ticker = Ticker('^GSPC')
	hist = ticker.history(period='1d')

	if not hist.empty:
		return True
	else:
		return False
	
def log_msg(message: str):
	'''
	Creates an formatted message for the logger
	'''
	return (f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - {message}')

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='database.log', encoding='utf-8', level=logging.WARN)

# Open config
with open('config.json') as f:
	config = json.load(f)

# Create a YahooClient
yahoo_client = YahooClient()

# Set up web scraper
scraper = NewsWebScraper()

# Set up Llama for sentiment analysis
llama = LlamaChat()

def daily_protocall():
	'''
	Collects data on the specified ticker and analyzes it
	'''

	# Iterate through every ticker in the S&P 500
	for ticker in modules.tickers.TICKERS:
		logger.warning(log_msg(f'PULL: {ticker.upper()}'))

		# Get the daily market data
		result, current_data = yahoo_client.current(ticker)

		if result == 1: # 1 = Error
			logger.error(log_msg(current_data))

			return False

		# Collect news information
		result, scraped_sites = scraper.scrape_from_yf(ticker)

		if result == 1: # 1 = Error
			logger.error(log_msg(scraped_sites))

			return False

		# Create a variable to store the average sentiment
		sentiments = []

		for site in scraped_sites:
			# Create a prompt to get the sentiment of the stock
			sentiment_prompt = f'''
				Imagine you are a human who is hoping to buy {ticker} stock.
				You want to read articles, and rate your interest in buying {ticker}
				on a scale from 1-10 based on the readings of the article. A "1" is equivalent to no
				interest in buying {ticker}, and a "10" means you have an 100% interest
				in buying {ticker}.

				You also want to to ignore as much advertising text as possible within the article, as this information is
				irrelevant to the analysis of the performance of {ticker}.

				If enough information about the sentiment can be derived, return only a number between 1-10, and nothing else.

				If enough information about the sentiment cannot be derived, return the word "NONE" and nothing else.

				Article below:

				{site.title}

				{site.content}
			'''

			# Store the sentiment in a list so we can average the sentiment over all stock
			try:
				sentiments.append(int(llama.prompt(sentiment_prompt)))
			except ValueError:
				logger.warning(log_msg(f'LLM caused value error while analyzing news'))

		# Get the average sentiment of the stock for today
		avg_sentiment = mean(sentiments)

		# Try and load saved historical data
		try:
			historical_data = pd.read_pickle(f'stockdata/{ticker}.pkl')
		except:
			# If no historical data exists, start storing
			# historical data from today
			historical_data = current_data

		# Create a new column to add the market sentiment
		historical_data['sentiment'] = avg_sentiment

		# Save the dataframe as a file
		historical_data.to_pickle(f'stockdata/{ticker}.pkl')

		# Test option: save to csv to get visual representation
		historical_data.to_csv(f'stockdata/csv/{ticker}.csv')

	# Save last update time in config
	with open('config.json', 'w') as f:
		config['LAST_PROTOCALL_UPDATE'] = str(date.today())

		json.dump(config, f, indent=4)

		return True

# Main logic
while True:
	# Log the bootup time
	logger.warning(log_msg('BOOT'))

	try:
		# Start only if market has been closed for an hour (since we want todays data as well)
		while not (datetime.now(pytz.timezone('US/Eastern')).hour < 9 or \
			(datetime.now(pytz.timezone('US/Eastern')).hour >= 17)):
				pass

		# If today is a weekend, do not run
		# Also, if there was a previous attempt, check if it is too early to attempt again
		if str(date.today()) != config['LAST_PROTOCALL_UPDATE'] and is_market_open():
			protocall_complete = daily_protocall()

			if protocall_complete:
				logger.warning(log_msg('Protocall COMPLETED'))
			else:
				logger.error(log_msg('Protocall FAILED'))
				time.sleep(1 * 3600) # Sleep an hour and try again
	except KeyboardInterrupt:
		break