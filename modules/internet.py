import pandas as pd

import requests
from bs4 import BeautifulSoup
import yfinance as yf

import json
import os

from datetime import date, datetime, timezone

def error_message(file: str, message: str, error: Exception):
	'''
	Returns a formatted string that can be used to log errors correctly
	'''
	
	return f'[{file}]: {message} *** {str(error)} -> [Line: {error.__traceback__.tb_lineno}]'

class YahooClient:
	'''
	# YahooClient
	Uses the `yfinance` library to get market data for a stock trading AI
	'''
	def current(self, ticker: str):
		'''
		Returns daily valuation metrics of a stock
		'''
		# Create a `yfinance.Ticker` object for the desired company
		yf_ticker = yf.Ticker(ticker)

		# Get info about the company
		try:
			info = yf_ticker.info
		except Exception as e:
			return (1,
				error_message('internet.py', f'{ticker.upper()} - Could not pull data', e)
			)

		# Combine valuation metrics into a dataframe
		try:
			# Use `info.get(_, -1)` so that if there is no data metric for a specific ticker, it defaults to "-1"
			data = {
				'date': [date.today()],
				'open': [info.get('open', -1)],
				'dayHigh': [info.get('dayHigh', -1)],
				'dayLow': [info.get('dayLow', -1)],
				'previousClose': [info.get('previousClose', -1)],
				'dividendRate': [info.get('dividendRate', -1)],
				'dividendYield': [info.get('dividendYield', -1)],
				'payoutRatio': [info.get('payoutRatio', -1)],
				'beta': [info.get('beta', -1)],
				'trailingPE': [info.get('trailingPE', -1)],
				'forwardPE': [info.get('forwardPE', -1)],
				'marketCap': [info.get('marketCap', -1)],
				'fiftyTwoWeekLow': [info.get('fiftyTwoWeekLow', -1)],
				'fiftyTwoWeekHigh': [info.get('fiftyTwoWeekHigh', -1)],
				'priceToSalesTrailing12Months': [info.get('priceToSalesTrailing12Months', -1)],
				'fiftyDayAverage': [info.get('fiftyDayAverage', -1)],
				'twoHundredDayAverage': [info.get('twoHundredDayAverage', -1)],
				'ebitda': [info.get('ebitda', -1)],
				'totalDebt': [info.get('totalDebt', -1)],
				'quickRatio': [info.get('quickRatio', -1)],
				'currentRatio': [info.get('currentRatio', -1)],
				'totalRevenue': [info.get('totalRevenue', -1)],
				'debtToEquity': [info.get('debtToEquity', -1)],
				'revenuePerShare': [info.get('revenuePerShare', -1)],
				'returnOnAssets': [info.get('returnOnAssets', -1)],
				'returnOnEquity': [info.get('returnOnEquity', -1)],
				'grossProfits': [info.get('grossProfits', -1)],
				'freeCashflow': [info.get('freeCashflow', -1)],
				'operatingCashflow': [info.get('operatingCashflow', -1)],
				'earningsGrowth': [info.get('earningsGrowth', -1)],
				'revenueGrowth': [info.get('revenueGrowth', -1)],
				'grossMargins': [info.get('grossMargins', -1)],
				'ebitdaMargins': [info.get('ebitdaMargins', -1)],
				'operatingMargins': [info.get('operatingMargins', -1)],
				'bookValue': [info.get('bookValue', -1)],
				'priceToBook': [info.get('priceToBook', -1)],
				'netIncomeToCommon': [info.get('netIncomeToCommon', -1)],
				'trailingEps': [info.get('trailingEps', -1)],
				'forwardEps': [info.get('forwardEps', -1)],
				'enterpriseValue': [info.get('enterpriseValue', -1)],
				'enterpriseToRevenue': [info.get('enterpriseToRevenue', -1)],
				'enterpriseToEbitda': [info.get('enterpriseToEbitda', -1)],
				'epsCurrentYear': [info.get('epsCurrentYear', -1)],
				'priceEpsCurrentYear': [info.get('priceEpsCurrentYear', -1)],
				'trailingPegRatio': [info.get('trailingPegRatio', -1)],
			}
		except KeyError as e:
			# Key error will usually mean the user did not enter the ticker name corectly
			return (1,
				error_message('internet.py', f'{ticker.upper()} - Unable to create price DataFrame', e)
			)

		return (0, pd.DataFrame(data))

class NewsWebScraper:
	'''
	# NewsWebScaper

	Class used to get the content of news webpages provided by `yfinance`
	'''
	def scrape_from_yf(self, ticker: str):
		'''
		Scrapes websites provided by `yfinance` and returns a list of 
		`NewsWebPage` objects
		'''

		# Search the news on yfinance
		try:
			yf_news = yf.Search(ticker, news_count=10).news
		except Exception as e:
			return (1,
				error_message('internet.py', f'{ticker.upper()} - Could not pull news data', e)
			)

		# Make a list to store each scraped site
		scraped_sites = []

		# User-Agent headers
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
		}

		# Fetch historical news
		try:
			news_data = pd.DataFrame.from_dict(yf_news)[['title','publisher','providerPublishTime','link']]
		except Exception as e:
			return (1,
				error_message('internet.py', f'{ticker.upper()} - Could not create DataFrame from news source', e)
			)

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
			if data.status_code == 200:
				
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
							news_data['title'][i],
							news_data['publisher'][i],
							news_data['providerPublishTime'][i],
							news_content,
							news_data['link'][i]
						)
					)

		# Return the scraped sites only if there are enough "NewsWabPage" objects
		if len(scraped_sites) == 0:
			return (1, error_message('internet.py', f'{ticker.upper()} - Could not pull sufficient news data', e))
		
		return (0, scraped_sites)

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