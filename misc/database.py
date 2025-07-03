from modules.internet import YahooClient, NewsWebScraper
from modules.llm import LlamaChat

import modules.tickers
from yfinance import Ticker

from datetime import datetime, date
from time import sleep
import pytz

import pandas as pd
from statistics import mean, StatisticsError

import json
import logging

def is_market_open():
	if not Ticker('^GSPC').history(period='1d').empty:
		return True
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

def run_protocall(ticker: str):
	'''
	Collects data on the specified ticker, analyzes it, and saves it as a pandas dataframe
	'''

	# Get the daily market data
	result, current_data = yahoo_client.current(ticker)

	if result == 1: # 1 = Error
		logger.error(log_msg(current_data))

		return False

	# Collect news information
	result, scraped_sites = scraper.scrape_from_yf(ticker)

	if result == 1: # 1 = Error

		# If there is no news data, set `scraped_sites` to an empty list
		logger.warning(log_msg(scraped_sites))

		scraped_sites = []

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
			# ValueError just means that ollama returned data that was not an integer
			pass

	# Get the average sentiment of the stock for today
	try:
		avg_sentiment = mean(sentiments)
	except StatisticsError as e:

		# If an average sentiment could not be calculated, set the average sentiment to 5
		# TODO: Implement better way to deal with this

		logger.warning(log_msg(f'{ticker} - StatisticsError: Could not obtain average sentiment, "{e}"'))
		avg_sentiment = 5
	
	except AttributeError as e:
		logger.error(log_msg(f'{ticker} - AttributeError: Could not obtain average sentiment, "{e}"'))
		return False

	# Try and load saved historical data
	try:
		historical_data = pd.read_csv(f'stockdata/{ticker}.csv')

		# Create a new column to add the market sentiment
		current_data['sentiment'] = avg_sentiment

		# Check if data already exists for the current day
		if current_data['date'][0] == historical_data['date'][len(historical_data) - 1]:
			
			# If there is already data for the current day, ignore the pulled data
			logger.warning(log_msg(f'{ticker} - Data already exists for curent day'))

		else:

			# If there is not data for the current day, make a new entry
			historical_data = pd.concat([historical_data, current_data], ignore_index=True)

	except Exception as e:
		# If no historical data exists, start storing
		# historical data from today
		historical_data = current_data

		# Create a new column to add the market sentiment
		historical_data['sentiment'] = avg_sentiment

	# Save the dataframe as a file
	historical_data.to_csv(f'stockdata/{ticker}.csv', index=False)

	# If everything works without error, return "True"
	return True

'''
#########################
DATABASE CODE STARTS HERE
#########################
'''

# Log the bootup time
logger.warning(log_msg('BOOT'))

# Main logic
while True:
	# Start only if market has been closed for an hour (since we want todays data as well)
	try:
		while (
			datetime.now(pytz.timezone('US/Eastern')).hour > 9 and 
			datetime.now(pytz.timezone('US/Eastern')).hour <= 1
		):
			pass

	except KeyboardInterrupt:
		logger.warning(log_msg('KeyboardInterrupt'))
		break


	try:
		# If the market was not ope today, do not run
		# Also, if there was a previous attempt, check if it is too early to attempt again
		if str(date.today()) != config['LAST_PROTOCALL_UPDATE'] and is_market_open():

			# Log when daily protocall starts
			logger.warning(log_msg('START PROTO'))

			for ticker in modules.tickers.TICKERS:
			
				# Iterate through every ticker in the S&P 500
				logger.warning(log_msg(f'{ticker.upper()} - PULL'))

				protocall_complete = run_protocall(ticker)

				if protocall_complete:
					logger.warning(log_msg(f'{ticker.upper()} - SUCCESS'))
					
					# Sleep for one minute to avoid rate-limiting errors
					sleep(60)
				else:
					logger.warning(log_msg(f'{ticker.upper()} - FAIL'))
					sleep(1 * 3600) # Sleep an hour and try again

			# Save last update time in config
			with open('config.json', 'w') as f:
				config['LAST_PROTOCALL_UPDATE'] = str(date.today())

				json.dump(config, f, indent=4)

			# Log when daily protocall ends
			logger.warning(log_msg('END PROTO'))

	except KeyboardInterrupt:
		logger.warning(log_msg('KeyboardInterrupt'))
		break