'''
Module that manages log files for the entire aplication
'''

import logging
from datetime import datetime, date

def _m(message: str):
	'''
	Creates a formatted message for the logger
	'''
	return (f'{str(date.today())} @ {datetime.now().hour}:{datetime.now().minute} - {message}')

class logger:
	'''
	# logger

	Main logging class
	'''

	def __init__(self, program_name: str, file_name: str):
		self.logger = logging.getLogger(program_name)

		logging.basicConfig(
			filename=f'logs/{file_name}.log',
			encoding='utf-8'
		)

	def debug(self, message: str):
		'''
		Logs a message with level DEBUG
		'''
		self.logger.warning(_m(message))

	def warning(self, message: str):
		'''
		Logs a message with level WARNING
		'''
		self.logger.warning(_m(message))
	
	def error(self, message: str):
		'''
		Logs a message with level ERROR
		'''
		self.logger.error(_m(message))