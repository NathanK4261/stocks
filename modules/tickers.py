'''
# tickers
A list containing the ticker symbols of every stock in the S&P 500

Yes, it does update the list every time...
'''
from pandas import read_excel
from .internet import YahooClient as yc

TICKERS = []

# A list of tickers not allowed to be used
banned_tickers = ['CASH_USD', '-', 'BRK.B', 'BRK.A']


# Updates "TICKERS" to include the latest companies in the S&P 500
# Source: https://www.ssga.com/us/en/intermediary/etfs/funds/spdr-sp-500-etf-trust-spy

url = 'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'
holdings = read_excel(url, engine='openpyxl', skiprows=4).dropna()['Ticker']

for ticker in holdings:
	if ticker not in banned_tickers:
		TICKERS.append(ticker)