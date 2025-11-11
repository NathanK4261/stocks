import json
import pandas as pd

from sklearn.preprocessing import StandardScaler

import torch

from numpy import array

# Open config
with open('config.json') as f:
	config = json.load(f)

# The neural network
class StockNet(torch.nn.Module):
	'''
	# StockNet

	An LSTM neural network for predicting weather to buy/sell a stock
	'''
	def __init__(self):
		super(StockNet, self).__init__()

		self.lstm = torch.nn.LSTM(input_size=31, hidden_size=50, num_layers=2, batch_first=True)
		self.linear = torch.nn.Linear(
			50, # input dimensions
			1 # output dimension(s)
		)

	def forward(self, x, hidden_state=None, cell_state=None):
		'''
		Method for runinng one "forward pass" of the model

		- `hidden_state` = The models "short term memory" (what it is using to make an immediate prediction)
		- `cell_state` = The models "long term memory" (important information used for making predictions)
		'''
		if hidden_state is None or cell_state is None:

			# Create blank hidden state
			hidden_state = torch.zeros(
				2, # num_layers
				x.size(0),
				50 # hidden_size
			).to(x.device)
			
			# Create blank cell state
			cell_state = torch.zeros(
				2, # num_layers
				x.size(0),
				50 # hidden_size
			).to(x.device)

		# Outputs (out = ALL hidden states) (hs = new hidden state) (cs = new cell state)
		out, (hs, cs) = self.lstm(x, (hidden_state, cell_state))

		out = self.linear(out[:, -1, :]) # Take last time step

		# Use sigmoid function to return a value 0 or 1
		out = torch.sigmoid(out)

		return out, hs, cs

# Create a custom Dataset() class
class StockNetDataset(torch.utils.data.Dataset):
	def __init__(self, x: torch.Tensor, y: torch.Tensor):
		self.x = x
		self.y = y

	def __len__(self):
		return len(self.y)
	
	def __getitem__(self, index):
		return self.x[index], self.y[index].unsqueeze(-1)
	
def StockNet_prediction(ticker: str, device: str):
	'''
	Uses `StockNet` to make a prediction about a specific stock
	'''

	# Load training data
	try:
		training_data = pd.read_csv('stockdata/training_data.csv')
	except FileNotFoundError:
		return False

	# Get only input data for StockNet
	inp = training_data.loc[training_data['ticker'] == ticker.upper()].drop(['ticker'], axis=1).astype('float32').reset_index(drop=True)

	# Obtain the last 2 days data for the particular stock, and convert into a pytorch tensor
	last_2_days = inp.iloc[len(inp)-2:]
	X, y = [], []
	y.append(last_2_days['investmentDecision'])
	X.append(last_2_days.drop('investmentDecision', axis=1))

	# Create dataloader of data from the last 2 days
	dataloader = torch.utils.data.DataLoader(
		StockNetDataset(
			torch.from_numpy(array(X)).to(device),
			torch.from_numpy(array(y)).to(device)
		)
	)

	# Load StockNet
	try:
		# Try and load a previous version
		model = StockNet().to(device)
		model.load_state_dict(torch.load('StockNet/model',weights_only=True))
	except:
		print('No StockNet model avaliable to load, skipping...')
		model = StockNet().to(device)

	# Run prediction on our data
	model.eval()

	# Disable gradient computation and reduce memory consumption.
	with torch.no_grad():
		for _, data in enumerate(dataloader):
			inputs, move = data
			output, _, _ = model(inputs)

	# Convert raw logit to probability and prediction
	prediction = output.item()

	return prediction
