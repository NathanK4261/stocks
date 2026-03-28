import requests
from bs4 import BeautifulSoup

from pandas import DataFrame
import pandas_market_calendars as mcal

import yfinance as yf
import yfinance.exceptions

import datetime

from . import valuations
from . import errors

def market_open():
	'''
	Returns true if the stock market was open today

	Does NOT tell you if market is open at the current time, just if the market was open on the current day
	'''
	
	try:
		# Get current date
		day = str(datetime.date.today())

		# Get the NYSE calendar from the current day
		result = mcal.get_calendar("NYSE").schedule(start_date=day, end_date=day)

	except Exception as e:
		raise errors.error('internet.py', 'Error while checking if market is open', e)

	# If the calendar is not empty, the market is/was open on the current day
	return result.empty == False

class YahooStockClient:
	'''
	# YahooStockClient
	Uses the `yfinance` library to get market data for a stock trading AI
	'''

	def current(self, ticker: str, set_date = datetime.date.today()):
		'''
		Returns daily valuation metrics of a stock
		
		:param self:
		:param ticker: The ticker symbol of the company
		:type ticker: str
		:param set_date: Defaults to the current date, can be manually set if needed
		:type set_date: date
		'''

		# Get info about the company
		try:
			info = yf.Ticker(ticker).info

		except yfinance.exceptions.YFRateLimitError:
			raise errors.error('internet.py', 'Rate limiting implemented, try again', e)

		except Exception as e:
			raise errors.error('internet.py', 'Could not pull data', e)

		# Combine valuation metrics into a single dict
		data = {}
		data['ticker'] = ticker
		data['date'] = str(set_date)

		for value, _ in valuations.yf_values:

			# Ignore keys that are not a part of the yfinance API data
			if value in ['ticker','date','id']:
				continue

			try:
				# Use `info.get(value, None)` so that if there is no data metric 
				# for a specific ticker, it defaults to "None"
				data[value] = [info.get(value, None)]

			except Exception as e:
				# Key error will usually mean the user did not enter the ticker/value name corectly
				raise errors.error('internet.py', 'Unable to create price dict', e)
			
		try:
			data_df = DataFrame(data, index=None)
		except Exception as e:
			raise errors.error('internet.py', 'Unable to create price DataFrame', e)

		return data_df

	def scrape_from_yf(self, ticker: str):
		'''
		Scrapes websites provided by `yfinance` and returns a list of 
		`NewsWebPage` objects
		'''

		# Search the news on yfinance
		try:
			yf_news = yf.Search(ticker, news_count=3).news

		except Exception as e:
			raise errors.error('internet.py', 'Could not pull news data', e)

		except yfinance.exceptions.YFRateLimitError:
			raise errors.error('internet.py', 'Rate limiting implemented, try again', e)

		# Make a list to store each scraped site
		scraped_sites = []

		# User-Agent headers
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
		}

		# Fetch historical news
		try:
			news_data = DataFrame.from_dict(yf_news)[['title','publisher','providerPublishTime','link']]
		
		except Exception as e:
			raise errors.error('internet.py', f'Could not create DataFrame for {ticker} from news source', e)

		# Get the html content of each webpage
		for i in range(len(news_data)):

			# Fetch the website data
			try:
				data = requests.get(news_data['link'][i],
					allow_redirects=True,
					headers=headers
				)
			except:
				# No need to return error if site was unable to be reached, only
				# return error if no data was able to be pulled at all
				data = None

			# Verfiy that the site was cleanly retreived
			if data == None:
				pass
			elif data.status_code == 200:
				
				# Get the HTML content
				data = data.text

				# Parse the HTML content
				soup = BeautifulSoup(data, 'html.parser')

				# Attempt 1: Extract data from "<p>" tag
				# NOTE: 'yf-1pe5jgt' is a class where most text can be found on some articles
				news_content = ''
				for content in soup.find_all('p'):
					news_content += (content.text + ' ')

				# If the data scraped from the site is not empty, create a
				# "NewsWebPage" object and store the site information
				if len(news_content) != 0 or news_content is not None:
					
					scraped_sites.append(
						NewsWebPage(
							ticker,
							news_data['title'][i],
							news_content,
						)
					)

		# Return the scraped sites only if there are enough "NewsWabPage" objects
		if len(scraped_sites) == 0:
			raise errors.error('internet.py', 'Could not pull sufficient news data', e)
		
		return scraped_sites

class NewsWebPage:
		'''
		# NewsWebPage

		Class used to store data about different news web pages

		**NOTE:** This class is used in `NewsWebScraper`, so there is no need to 
		contruct objects using this class manually
		'''
		def __init__(self, ticker: str, title: str, content: str):
			self.ticker = ticker # The company ticker that the web page is talking about

			self.title = title # Title of the news article

			self.content = content # The content in the news article