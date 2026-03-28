'''
# valuations

A list that stores the name of each valuation metric in `yfinance`
'''

yf_values = [
	('date', 'TEXT'),
	('ticker', 'TEXT'),
	('industry', 'TEXT'),
	('sector', 'TEXT'),
	('previousClose', 'DOUBLE'),
	('regularMarketPrice', 'DOUBLE'),
	('open', 'DOUBLE'),
	('dayLow', 'DOUBLE'),
	('dayHigh', 'DOUBLE'),
	('beta', 'DOUBLE'),
	('trailingPE', 'DOUBLE'),
	('forwardPE', 'DOUBLE'),
	('volume', 'DOUBLE'),
	('averageVolume', 'DOUBLE'),
	('averageVolume10days', 'DOUBLE'),
	('marketCap', 'DOUBLE'),
	('fiftyTwoWeekLow', 'DOUBLE'),
	('fiftyTwoWeekHigh', 'DOUBLE'),
	('priceToSalesTrailing12Months', 'DOUBLE'),
	('fiftyDayAverage', 'DOUBLE'),
	('twoHundredDayAverage', 'DOUBLE'),
	('profitMargins', 'DOUBLE'),
	('shortRatio', 'DOUBLE'),
	('bookValue', 'DOUBLE'),
	('priceToBook', 'DOUBLE'),
	('earningsQuarterlyGrowth', 'DOUBLE'),
	('epsTrailingTwelveMonths', 'DOUBLE'),
	('epsForward', 'DOUBLE'),
	('enterpriseToRevenue', 'DOUBLE'),
	('quickRatio', 'DOUBLE'),
	('currentRatio', 'DOUBLE'),
	('returnOnAssets', 'DOUBLE'),
	('returnOnEquity', 'DOUBLE'),
	('trailingPegRatio', 'DOUBLE'),
	('sentiment', 'DOUBLE'),
]