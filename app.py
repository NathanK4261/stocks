'''
Flask server that posts updates on the stocks database
'''
from flask import Flask, Response

import pandas as pd

import json

with open('config.json') as f:
	config = json.load(f)

app = Flask(__name__)

@app.route("/")
def index():
	with open('database.log') as db_file:
		lines = db_file.readlines()

	lines = ''.join(lines)

	return Response(lines, mimetype='text/plain')