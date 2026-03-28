'''
# errors

Provides functions to display helpfull error messages in a uniform matter across all programs
'''

class error(Exception):
	'''
	# error
	Returns an `Exception` object that can be used to log errors correctly
	'''
	def __init__(self, file: str, message: str, error: Exception = None):
		self.file = file
		self.message = message
		self.error = error

		super().__init__(self.message)
		
	def __str__(self):
		if self.error == None:
			return f'{self.file}[UnkownError] "{self.message}" -> [Line: ???]'
		
		return f'{self.file}[{type(self.error).__name__}] "{self.message}" ({str(self.error)}) -> [Line: {self.error.__traceback__.tb_lineno}]'