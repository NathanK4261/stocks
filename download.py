from modules.internet import YahooClient, NewsWebScraper, market_open
import modules.tickers
import modules.datamanager
import modules.llm
from modules.errors import error_message

from datetime import datetime, date
from time import sleep
import pytz

from statistics import mean

import json
import logging
	
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

# Initialize ollama
llm = modules.llm.LlamaChat()

# Initialize database manager and news manager
db_manager = modules.datamanager.DatabaseManager()

# Create a YahooClient
yahoo_client = YahooClient()

# Set up web scraper
scraper = NewsWebScraper()

def run_protocall(ticker: str):
	'''
	Collects data on the specified ticker, analyzes it, and saves it as a pandas dataframe
	'''

	# Get the daily market data
	current_data = yahoo_client.current(ticker)

	if type(current_data) == str: # Error
		logger.error(log_msg(current_data))

		return False

	# Collect news information
	scraped_sites = scraper.scrape_from_yf(ticker)

	if type(scraped_sites) == str: # Error

		# If there is no news data, set `scraped_sites` to an empty list
		logger.error(log_msg(scraped_sites))

		scraped_sites = []

	# TODO: Get news sentiment
	sentiments = []

	# Iterate through each news article for the given ticker
	for news_site in scraped_sites:

		# Run the custom news prompt for the article
		site_sentiment = llm.news_prompt(news_site)

		# Warn user of missing sentiment in log file
		if type(site_sentiment) == str:
			print(site_sentiment)
			logger.warning(log_msg(site_sentiment))
			#sentiments.append(5) --> Could do this as an alternative, give a more neutral rating of the stock
		
		# If sentiment extracted correctly, add to "sentiments" list
		elif type(site_sentiment) == int():
			sentiments.append(site_sentiment)

	# Average the sentiments
	avg_sentiment = mean(sentiments)

	# Add sentiment to current data
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
try:
	if str(date.today()) != config['LAST_PROTOCALL_UPDATE'] and market_open():

		# Log when daily protocall starts
		logger.warning(log_msg(f'START PROTO ({len(modules.tickers.TICKERS)} Tickers)'))

		# Set a boolean in case we need to KeyboardInterrupt
		save_data = True

		for ticker in modules.tickers.TICKERS:
		
			attempts = 3

			while attempts > 0:
				# Iterate through every ticker
				
				#logger.warning(log_msg(f'{ticker.upper()} - PULL'))

				protocall_complete = run_protocall(ticker)

				if protocall_complete:
					logger.warning(log_msg(f'{ticker.upper()} - SUCCESS'))
					attempts = 0

				else:
					logger.warning(log_msg(f'{ticker.upper()} - FAIL'))
					sleep(60) # Sleep for a minute and try again

					attempts -= 1

		# Save last update time in config, but only if "save_data" is set to "True"
		if save_data:
			with open('config.json', 'w') as f:
				config['LAST_PROTOCALL_UPDATE'] = str(date.today())

				json.dump(config, f, indent=4)

		# Commit data to database
		db_manager.commit_all()

		# Log when daily protocall ends
		logger.warning(log_msg('END PROTO'))

	# If the market was closed today or if there was a previous attempt, log that there was no attempt today
	else:
		logger.warning(log_msg(f'PROTOCALL DID NOT RUN TODAY, MARKET WAS CLOSED OR DATA HAS ALREADY BEEN COLLECTED FOR: {str(date.today())}'))

except KeyboardInterrupt:
	logger.warning(log_msg('KeyboardInterrupt'))
	quit()