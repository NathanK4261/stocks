import modules.internet
import modules.logger
import modules.llm
import modules.datamanager
import modules.tickers
import modules.errors

from statistics import mean, StatisticsError

from datetime import datetime, date
import time
import pytz

import json

# Open config
with open('config.json') as f:
	config = json.load(f)

# Have variable that stores the date, so data collection retians the same date
set_date = date.today()

# Set up logger
logger = modules.logger.logger('download.py', 'download-'+str(set_date))

# Initialize ollama
llm = modules.llm.LlamaChat()

# Initialize database manager
dmanager = modules.datamanager.DataManager()

# Create a YahooStockClient
yahoo_client = modules.internet.YahooStockClient()

def download(ticker: str):
	'''
	Collects data on the specified ticker, analyzes it, and saves it as a pandas dataframe
	'''

	# Check to se if data exists for that day
	if dmanager.data_exists(set_date, ticker):
		return True

	# Get the daily market data
	try:
		current_data = yahoo_client.current(ticker, set_date)

	except modules.errors.error as e:
		logger.error(e)
		return False

	# Collect news information
	try:
		scraped_sites = yahoo_client.scrape_from_yf(ticker)
	
	except modules.errors.error as e:
		# If there is no news data, set `scraped_sites` to an empty list
		logger.error(e)
		scraped_sites = []

	# Create list to store sentiments
	sentiments = []

	# Iterate through every article
	for site in scraped_sites:

		# Obtain sentiment from article
		try:
			sentiment = llm.news_prompt(site)
		
		except modules.errors.error as e:

			# ValueError just means that there was no sentiment for the stock, so no need to log an error
			if not isinstance(e.error, ValueError):
				logger.error(e)

			# If there was an error, set the sentiment value to "None"
			sentiment = None

		if type(sentiment) == int: # Sentiment obtained correctly
			sentiments.append(sentiment)

	try:
		# Average sentiments
		avg_sentiment = mean(sentiments)

	except StatisticsError:
		logger.warning(f'Could not calculate average sentiment for {ticker}')
		
		# If there was no sentiment values in the list, just default to 5
		avg_sentiment = None

	# Update sentiment to caluclated sentiment
	current_data['sentiment'] = avg_sentiment
	
	# Add stockdata to database, and news data to dataframe
	try:
		dmanager.add_data(current_data)

	except modules.errors.error as e:
		logger.error(e)
		return False

	# If everything works without error, save data and return "True"
	dmanager.save()
	return True


# If the market was not open today, do not run
# Also, if there was a previous attempt, check if it is too early to attempt again
if set_date != config['LAST_PROTOCALL_UPDATE'] and modules.internet.market_open():

	# Start only if market has been closed for an hour
	while (
		datetime.now(pytz.timezone('US/Eastern')).hour > 9 and 
		datetime.now(pytz.timezone('US/Eastern')).hour <= 14
	):
		pass

	# Log when data collection starts
	logger.debug(f'START DATA COLLECTION ({len(modules.tickers.TICKERS)} Tickers)')
	
	completed = 0 # Use for logging how many companies completed

	# Iterate through every ticker
	for ticker in modules.tickers.TICKERS:

		# Collect data for specific ticker
		while True:
			try:
				protocol_complete = download(ticker)

				if protocol_complete:
					completed += 1
					logger.warning(f'{ticker.upper()} - SUCCESS ({completed}/{len(modules.tickers.TICKERS)})')
					break

				else:
					logger.warning(f'{ticker.upper()} - FAIL')

					# Sleep for 30 minutes and try again
					time.sleep(1800)
			except KeyboardInterrupt:
				logger.warning('KeyboardInterrupt')
				exit()

	# Log when data collection ends
	logger.debug('DATA COLLECTED')

	# Save last update time in config, but only if "save_data" is set to "True"
	with open('config.json', 'w') as f:
		config['LAST_PROTOCALL_UPDATE'] = str(set_date)

		json.dump(config, f, indent=4)

# If the market was closed today or if there was a previous attempt, log that there was no attempt today
else:
	logger.warning(f'PROTOCOL DID NOT RUN TODAY, MARKET IS CLOSED OR DATA HAS ALREADY BEEN COLLECTED FOR: {set_date}')