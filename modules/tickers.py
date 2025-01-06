'''
# tickers
A list containing the ticker symbols of every stock in the S&P 500

Yes, it does update the list every time...
'''
from pandas import read_excel

TICKERS = []


# Updates "TICKERS" to include the latest companies in the S&P 500
# Source: https://www.ssga.com/us/en/intermediary/etfs/funds/spdr-sp-500-etf-trust-spy

url = 'https://www.ssga.com/us/en/intermediary/etfs/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'
holdings = read_excel(url, engine='openpyxl', skiprows=4).dropna()['Ticker']

for ticker in holdings:
	if ticker != 'CASH_USD' or ticker != '-':
		TICKERS.append(ticker)