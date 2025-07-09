from modules.internet import YahooClient, NewsWebScraper
import modules.tickers

import pandas_market_calendars as mcal
from datetime import datetime, date
from time import sleep
import pytz

import pandas as pd
import json
import logging

def market_open():
	'''
	Returns true if the stock market was open today
	'''
	# Get current date
	day = str(date.today())

	# Get the NYSE calendar from the current day
	result = mcal.get_calendar("NYSE").schedule(start_date=day, end_date=day)

	# If the calendar is not empty, the market is/was open on the current day
	return result.empty == False
	
def log_msg(message: str):
	'''
	Creates an formatted message for the logger
	'''
	return (f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - {message}')

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename=f'logs/{str(date.today())}.log', encoding='utf-8', level=logging.WARN)

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

	# Check to see if data was already collected for the current day
	try:
		# Read from historical data
		historical_data = pd.read_pickle(f'stockdata/{ticker}.pkl')

		# Compare today's date to the latest saved date in the historical data
		if str(date.today()) == historical_data['date'][len(historical_data) - 1]:
			
			# If there is already data for the current day, ignore pulling data for today
			logger.warning(log_msg(f'{ticker} - Data already exists for curent day'))

			return True
	except FileNotFoundError:
		# We can ignore this error as it just means that there is no saved data on the specific ticker
		pass

	# Get the daily market data
	result, current_data = yahoo_client.current(ticker)

	if result == 1: # 1 = Error
		logger.error(log_msg(current_data))

		return False

	# Collect news information
	result, scraped_sites = scraper.scrape_from_yf(ticker)

	if result == 1: # 1 = Error

		# If there is no news data, set `scraped_sites` to an empty list
		logger.error(log_msg(scraped_sites))

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

		# Add our list of "NewsWebPage" objects to our current dataframe
		current_data['news'] = [scraped_sites]

		# If there is not data for the current day, make a new entry
		historical_data = pd.concat([historical_data, current_data], ignore_index=True)

	# If no historical data exists, start storing historical data from today
	except FileNotFoundError:

		# Add our list of "NewsWebPage" objects to our current dataframe
		current_data['news'] = [scraped_sites]

		# Set our historical dataframe to our current dataframe
		historical_data = current_data

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

# Start only if market has been closed for an hour (since we want todays data as well)
try:
	while (
		datetime.now(pytz.timezone('US/Eastern')).hour > 9 and 
		datetime.now(pytz.timezone('US/Eastern')).hour <= 1
	):
		pass

except KeyboardInterrupt:
	logger.warning(log_msg('KeyboardInterrupt'))
	exit()


# If the market was not open today, do not run
# Also, if there was a previous attempt, check if it is too early to attempt again
if str(date.today()) != config['LAST_PROTOCALL_UPDATE'] and market_open():

	# Log when daily protocall starts
	logger.warning(log_msg(f'START PROTO ({len(modules.tickers.TICKERS)} Tickers)'))

	# Set a boolean in case we need to KeyboardInterrupt
	save_data = True

	for ticker in modules.tickers.TICKERS:
	
		while True:
			try:
				# Iterate through every ticker
				
				#logger.warning(log_msg(f'{ticker.upper()} - PULL'))

				protocall_complete = run_protocall(ticker)

				if protocall_complete:
					logger.warning(log_msg(f'{ticker.upper()} - SUCCESS'))
					break
				else:
					logger.warning(log_msg(f'{ticker.upper()} - FAIL'))
					sleep(60) # Sleep for a minute and try again

			except KeyboardInterrupt:
				logger.warning(log_msg('KeyboardInterrupt'))
				save_data = False

	# Save last update time in config, but only if "save_data" is set to "True"
	if save_data:
		with open('config.json', 'w') as f:
			config['LAST_PROTOCALL_UPDATE'] = str(date.today())

			json.dump(config, f, indent=4)

	# Log when daily protocall ends
	logger.warning(log_msg('END PROTO'))

# If the market was closed today or if there was a previous attempt, log that there was no attempt today
else:
	logger.warning(log_msg(f'PROTOCALL DID NOT RUN TODAY, MARKET WAS CLOSED OR DATA HAS ALREADY BEEN COLLECTED FOR: {str(date.today())}'))