from modules.internet import YahooClient, NewsWebScraper

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
	else:

		# Extract only the text from each "NewsWebPage" object
		temp = []

		for site in scraped_sites:
			temp.append([site.title, site.content])

		scraped_sites = temp

	# Try and load saved historical data
	try:
		historical_data = pd.read_pickle(f'stockdata/{ticker}.pkl')

		# Check if data already exists for the current day
		if current_data['date'][0] == historical_data['date'][len(historical_data) - 1]:
			
			# If there is already data for the current day, ignore the pulled data
			logger.warning(log_msg(f'{ticker} - Data already exists for curent day'))

		else:
			# Add our list of "NewsWebPage" objects to our current dataframe
			current_data['news'] = [scraped_sites]

			# If there is not data for the current day, make a new entry
			historical_data = pd.concat([historical_data, current_data], ignore_index=True)

	except Exception as e:
		# If no historical data exists, start storing historical data from today
		historical_data = current_data

		# Add our list of "NewsWebPage" objects to our current dataframe
		current_data['news'] = [scraped_sites]

	# Save the dataframe as a file
	historical_data.to_pickle(f'stockdata/{ticker}.pkl')

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
					#sleep(60)
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