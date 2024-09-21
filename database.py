from modules.internet import TiingoClient, NewsWebScraper
from modules.llm import LlamaChat

from datetime import datetime, date
import time
import pytz

import pandas as pd

from statistics import mean

import json
import logging

def is_weekend(date):
	try: 
		# Use isoweekday() to get the weekday (Monday is 1 and Sunday is 7)
		day_of_week = (date.weekday() + 1) % 7  # Convert Sunday from 6 to 0
			
		# Determine if it's a weekday or a weekend
		if 0 < day_of_week <= 5:
			return False
		else:
			return True
			
	except ValueError as e:
		print(f"Error: {e}")

# Create a logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='database.log', encoding='utf-8', level=logging.WARN)

# Open config
with open('config.json') as f:
	config = json.load(f)

# Create a TiingoClient
tiingo_client = TiingoClient()

# Set up web scraper
scraper = NewsWebScraper()

# Set up Llama for sentiment analysis
llama = LlamaChat()

def daily_protocall():
	'''
	Collects data on the specified ticker and analyzes it
	'''

	# Get the daily market data
	df = tiingo_client.get_daily_market_data()

	if df is None:
		return False # Exit the protocall if there is no data collected

	# Collect news information
	scraped_sites = scraper.scrape_from_yf()

	# Create a variable to store the average sentiment
	sentiments = []

	for site in scraped_sites:
		# Create a prompt to get the sentiment of the stock
		sentiment_prompt = f'''
Imagine you are a human who is hoping to buy {config['TICKER']} stock.
You want to read articles, and rate your interest in buying {config['TICKER']}
on a scale from 1-10 based on the readings of the article. A "1" is equivalent to no
interest in buying {config['TICKER']}, and a "10" means you have an 100% interest
in buying {config['TICKER']}.

Return only a number between 1-10, and nothing else.

Article below:

{site.content}
'''

		# Store the sentiment in a list so we can average the sentiment over all stock
		try:
			sentiments.append(int(llama.prompt(sentiment_prompt)))
		except ValueError:
			pass

	# Get the average sentiment of the stock for today
	avg_sentiment = mean(sentiments)

	# Try and load saved historical data
	try:
		historical_data = pd.read_pickle(f'stockdata/{config['TICKER']}/{config['TICKER']}.pkl')
	except:
		# If no historical data exists, start storing
		# historical data from today
		historical_data = df

	# Create a new column to add the market sentiment
	historical_data['sentiment'] = avg_sentiment

	# Save the dataframe as a file
	historical_data.to_pickle(f'stockdata/{config['TICKER']}/{config['TICKER']}.pkl')
	historical_data.to_csv(f'stockdata/{config['TICKER']}/{config['TICKER']}.csv', index=False)

	# Save last update time in config
	with open('config.json', 'w') as f:
		config['LAST_PROTOCALL_UPDATE'] = str(date.today())

		json.dump(config, f, indent=4)

		return True

# Main logic
def main():
	try:
		# Start if market has been closed for an hour (since we want todays data as well)
		while not (datetime.now(pytz.timezone('US/Eastern')).hour < 9 or \
			(datetime.now(pytz.timezone('US/Eastern')).hour >= 17)):
				pass

		# If today is a weekend, do not run
		# Also, if there was a previous attempt, check if it is too early to attempt again
		if not is_weekend(date.today()) and str(date.today()) != config['LAST_PROTOCALL_UPDATE']:
			protocall_complete = daily_protocall()

			if protocall_complete:
				logger.warning(f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - Protocall COMPLETED')
			else:
				logger.error(f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - Protocall FAILED')
				time.sleep(1 * 3600) # Sleep an hour and try again
	except KeyboardInterrupt:
		return 1

while True:
	result = main()

	if result == 1:
		break