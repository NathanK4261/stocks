from datetime import datetime

import ollama

from httpx import ConnectError

class LlamaPrompt:
	'''
	Stores information on specific prompts
	'''
	def __init__(self, model: str, prompt: str, response: str):
		self.timestamp = { # Stores the exact data and time captured (with timezone)
			'YEAR':datetime.now().year,
			'MONTH':datetime.now().month,
			'DAY':datetime.now().day,
			'HOUR':datetime.now().hour,
			'MINUTE':datetime.now().minute,
			'SECOND':datetime.now().second
		}
		self.timestamp['DATE_FORMATTED'] = f'{datetime.now().year}-{datetime.now().month}-{datetime.now().day} ({self.timestamp['HOUR']}:{self.timestamp['MINUTE']}:{self.timestamp['SECOND']})'

		self.model = model # The model used in the prompt
		self.prompt = prompt # The prompt the user provided
		self.response = response # The response from the LLM


class LlamaChat:
	'''
	# LlamaChat
	Used to access and talk to ollama LLM's in python
	'''
	def __init__(self, model: str = 'llama3.1:70b', prompting: bool = False):
		# Create a boolean to enable/disable llama prompting
		self.prompting = prompting

		models = []
		try:
			for ollama_model in ollama.list()['models']:
				models.append(ollama_model['name'])
		except ConnectError:
			print('Error connecting to ollama servers')
			exit(1)

		if model in models:
			self.model = model
		else:
			while True:
				choice = input(f'Model "{model}" has not been downloaded\nDownload? [y/n] ')

				if choice.lower() == 'y':
					print('Downloading...')
					try:
						ollama.pull(model)
					except KeyboardInterrupt:
						exit(0)
					print('Added model:',model)
					break
				else:
					quit(1)

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
		if self.prompting:
			return str(response['message']['content']), LlamaPrompt(self.model,message,response['message']['content'])
		else:
			return str(response['message']['content'])