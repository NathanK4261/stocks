from datetime import datetime

import ollama

from httpx import ConnectError

from .internet import NewsWebPage
from . import errors


class LlamaChat:
	'''
	# LlamaChat
	Used to access and talk to ollama LLM's in python
	'''
	def __init__(self, model: str = 'llama3.3:70b'):

		# Check to see if the requested model is downloaded
		models = []
		try:
			for ollama_model in ollama.list()['models']:
				models.append(ollama_model.model)

		except ConnectError as e:
			raise errors.error('llm.py','Error connecting to ollama servers', e)

		if model in models:
			self.model = model

		else:

			# If the model is not downloaded, prompt user to download it
			while True:
				choice = input(f'Model "{model}" has not been downloaded\nDownload? [y/n] ')

				if choice.lower() == 'y':

					print('Downloading...')

					try:
						ollama.pull(model)
					except KeyboardInterrupt as e:
						raise errors.error('llm.py', 'User cancelled model download', e)
					
					print('Added model:',model)

					self.model = model
					break

				elif choice.lower() == 'n':
					raise errors.error('llm.py','User declined model download',)

	def prompt(self, message: str):
		'''
		Sends a prompt to the LLM and returns the response

		if `create_LlamaPrompt` is set to True, a 
		LlamaPrompt object will be returned as well
		'''
		response = ollama.chat(
			model=self.model, 
			messages=[{'role':'user','content':message}]
		)

		# Return the message
		return str(response['message']['content'])
		
	def news_prompt(self, site: NewsWebPage):
		'''
		A custom prompt that returns the sentiment of a company's stock based on the news site
		'''

		prompt = f'''
			\rHere is a news article on {site.ticker} stock:
			
			\rTitle: {site.title}

			\rBody: {site.content}

			\rStep 1: Read the article
			\rStep 2: Ignore any parts of the article that do not provide insight into {site.ticker} stock (things like advertisements)
			\rStep 2: Identify what parts of the article convey an opinion about the stocks.
			\rStep 3: On a scale of 1-10, rate the average "sentiment" of those opinions
			\rStep 4: Return the number (betwen 1-10) that you thought of. ONLY RETURN TO ME A NUMBER!
			\rRemember: Sometimes the article may not talk about {site.ticker} stock, but may give information that could have impacts on the stock price. Try to use as much info as possible to rate the sentiment 1-10
			\rNote: If there was not enough infomration in the article to obtain a "number", return me only the word "NONE", and nothing else

			\rNow, follow these steps to derive the sentiment of {site.ticker} stock
		'''
		
		try:
			sentiment = int(self.prompt(prompt))
		
		except ValueError as e:
			raise errors.error('llm.py', f'Could not obtain sentiment for news article on {site.ticker}', e)
		except Exception as e:
			raise errors.error('llm.py', f'Unknown error while obtaining sentiment on {site.ticker}', e)
		
		return sentiment