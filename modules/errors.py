'''
# errors

Provides functions to display helpfull error messages in a uniform matter across all programs
'''

def error_message(file: str, message: str, error: Exception):
	'''
	Returns a formatted string that can be used to log errors correctly
	'''
	
	return f'[{file}]: {type(error).__name__} - {message} *** {str(error)} -> [Line: {error.__traceback__.tb_lineno}]'