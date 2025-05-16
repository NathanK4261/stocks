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
	def __init__(self):
		with open('config.json') as f:
			config = json.load(f)

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
				error_message('internet.py', f'Could not pull data for [{ticker.upper()}]',e)
			)

		# Combine valuation metrics into a dataframe
		try:
			data = {'date': [str(date.today())],
				'open': [info['open']],
				'high': [info['dayHigh']],
				'low': [info['dayLow']],
				'close': [info['previousClose']],
				'volume': [info['volume']],
				'trailingEps': [info['trailingEps']],
				'forwardEps': [info['forwardEps']],
				'trailingPE': [info['trailingPE']],
				'forwardPE': [info['forwardPE']],
				'priceToBook': [info['priceToBook']],
				'marketCap': [info['marketCap']],
				'fiftyDayAverage': [info['fiftyDayAverage']],
				'twoHundredDayAverage': [info['twoHundredDayAverage']]
			}
		except KeyError as e:
			# Key error will usually mean the user did not enter the ticker name corectly
			return (1,
				error_message('internet.py', f'Unable to create price DataFrame for [{ticker.upper()}]', e)
			)

		return (0, pd.DataFrame(data))

class NewsWebScraper:
	'''
	# WebScaper

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
				error_message('internet.py', f'Could not pull news data for [{ticker.upper()}]', e)
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
				error_message('internet.py', 'Could not create DataFrame from news source', e)
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
			return (1, 
				error_message('internet.py', f'Could not pull sufficient news data for [{ticker.uper()}]', e)
			)
		
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

class OllamaAPI:
	'''
	# OllamaAPI
	Class used to talk to the provided Ollama API endpoint

	NOTE: This endpoint is not secured unless done so by an outside party, do not 
	share sensitive information unless you are sure nobody can access it!
	'''
	def __init__(self, server_hostname:str, ollama_model:str):
		self.url = f"http://{server_hostname}:11434/api/generate" # API Endpoint to Ollama

		self.model = ollama_model

		self.headers={
			"Content-Type":"application/json"
		}

	def send_message(self, message:str):
		'''
		Sends a message to the Ollama API
		'''

		# Create our POST data
		data = {
			"model":self.model,
			"prompt":message,
			"stream":False
		}

		# Post our response to the Ollama API
		response = requests.post(self.url, headers=self.headers, data=json.dumps(data))

		# Return our data, or a status code indicating the error
		if response.status_code == 200:
			response = response.text
			response = json.loads(response)
			return str(response['response'])
		else:
			return response.status_code