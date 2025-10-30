from modules.internet import YahooClient, NewsWebScraper, market_open
import modules.tickers
import modules.datamanager
import modules.llm
from modules.errors import error_message

from datetime import datetime, date
from time import sleep
import pytz

from statistics import mean, StatisticsError

import json
import logging
import pickle

# Have variable that stores the date, so data collection retians the same date
set_date = str(date.today())

def log_msg(message: str):
	'''
	Creates a formatted message for the logger
	'''
	return (f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - {message}')

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename=f'logs/{set_date}.log', encoding='utf-8', level=logging.WARN)

# Open config
with open('config.json') as f:
	config = json.load(f)

# Initialize ollama
llm = modules.llm.LlamaChat()

# Initialize database manager
db_manager = modules.datamanager.DatabaseManager()
db_manager.new_table()

# Create a YahooClient
yahoo_client = YahooClient()

# Set up web scraper
scraper = NewsWebScraper()

def run_protocol(ticker: str):
	'''
	Collects data on the specified ticker, analyzes it, and saves it as a pandas dataframe
	'''

	# Get the daily market data
	current_data = yahoo_client.current(ticker, set_date)

	if type(current_data) == str: # Error
		logger.error(log_msg(current_data))

		return False

	# Collect news information
	scraped_sites = scraper.scrape_from_yf(ticker)

	if type(scraped_sites) == str: # Error

		# If there is no news data, set `scraped_sites` to an empty list
		logger.error(log_msg(scraped_sites))

		scraped_sites = []

	# Pickle news information and store it as a BLOB in SQL
	current_data['news'] = pickle.dumps(scraped_sites)

	# Create list to store sentiments
	sentiments = []

	# Iterate through every article
	for site in scraped_sites:

		# Obtain sentiment from article
		sentiment = llm.news_prompt(site)

		if type(sentiment) == int: # Sentiment obtained correctly
			sentiments.append(sentiment)

	try:
		# Average sentiments
		avg_sentiment = mean(sentiments)

	except StatisticsError:
		# If there was no sentiment values in the list, just default to 5
		avg_sentiment = 5

	# Update sentiment to caluclated sentiment
	current_data['sentiment'] = avg_sentiment
	
	# Add stockdata to database, and news data to dataframe
	result = db_manager.add_data(current_data)

	if type(result) == str: # Error
		logger.error(log_msg(result))

		return False

	# If everything works without error, return "True"
	return True

'''
#########################
MAIN CODE STARTS HERE
#########################
'''

# Start only if market has been closed for an hour (since we want todays data as well)
while (
	datetime.now(pytz.timezone('US/Eastern')).hour > 9 and 
	datetime.now(pytz.timezone('US/Eastern')).hour <= 17
):
	pass


# If the market was not open today, do not run
# Also, if there was a previous attempt, check if it is too early to attempt again
if set_date != config['LAST_PROTOCOL_UPDATE'] and market_open():

	# Log when data collection starts
	logger.warning(log_msg(f'START DATA COLLECTION ({len(modules.tickers.TICKERS)} Tickers)'))

	# Iterate through every ticker
	for ticker in modules.tickers.TICKERS:

		# Collect data for specific ticker
		protocol_complete = run_protocol(ticker)

		if protocol_complete:
			logger.warning(log_msg(f'{ticker.upper()} - SUCCESS'))

		else:
			logger.warning(log_msg(f'{ticker.upper()} - FAIL'))

			# Sleep for 2 minutes and try again
			sleep(120)

			protocol_complete = run_protocol(ticker)

			if protocol_complete:
				logger.warning(log_msg(f'{ticker.upper()} - SUCCESS'))
			else:
				logger.warning(log_msg(f'{ticker.upper()} - FAIL x2'))

	# Log when data collection ends
	logger.warning(log_msg('DATA COLLECTED'))

	# Disconnect from database
	db_manager.disconnect()

	# Save last update time in config, but only if "save_data" is set to "True"
	with open('config.json', 'w') as f:
		config['LAST_PROTOCOL_UPDATE'] = set_date

		json.dump(config, f, indent=4)

# If the market was closed today or if there was a previous attempt, log that there was no attempt today
else:
	logger.warning(log_msg(f'PROTOCOL DID NOT RUN TODAY, MARKET WAS CLOSED OR DATA HAS ALREADY BEEN COLLECTED FOR: {set_date}'))