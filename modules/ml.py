from torch.utils.data import Dataset
from torch import Tensor, tensor, load, float32, long
from torch.nn import LSTM, Linear, Module, CrossEntropyLoss
from torch.optim import SGD

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from pandas import DataFrame

import json

# Open config
with open('config.json') as f:
	config = json.load(f)

class MLTools:
	def __init__(self, device: str = 'cpu', manual_init: bool = False):
		if not manual_init:
			# Create our model, loss function, and optimizer
			self.model = self.snet(device).to(device)
			self.loss_function = self.lfunc().to(device)
			self.optimizer = self.optim()

			# Create our scaler
			self.scaler = StandardScaler()

		# Set our device
		self.device = device

	def load_training_dataset(self, X: DataFrame, Y: DataFrame):
		'''
		Loads a dataset, splits it into training and validation sets, and standardizes it.

		NOTE: Returns in order: X_train, X_val, Y_train, Y_val
		'''
		# Split the data into train and test sets
		xt, xv, yt, yv = train_test_split(X, Y, test_size=0.2, shuffle=False)

		# Standardize the data
		xt = self.scaler.fit_transform(xt)
		xv = self.scaler.transform(xv)

		# Return tensors of the data
		return tensor(xt, dtype=float32, device=self.device), tensor(xv, dtype=float32, device=self.device), tensor(yt, dtype=long, device=self.device), tensor(yv, dtype=long, device=self.device)

	def snet(self, device):
		try:
			# Try and load a previous version of our model
			_model = StockNet(device)
			_model.load_state_dict(load('StockNet/model',weights_only=True))
			return _model
		except:
			print('No StockNet model avaliable to load, skipping...')
			return StockNet(device)
		
	def lfunc(self):
		# Create loss function
		return CrossEntropyLoss() # Used to calculate loss for classification tasks (buy stock, sell stock, hold assets)

	# Create optimizer
	def optim(self):
		try:
			# Try and load a previous version of our model
			_optimizer = SGD(self.model.parameters(), lr=config['LEARNING_RATE'], momentum=config['MOMENTUM'])
			_optimizer.load_state_dict(load('StockNet/optimizer',weights_only=True))
			return _optimizer
		except:
			print('No StockNet optimizer avaliable to load, skipping...')
			return SGD(self.model.parameters(), lr=config['LEARNING_RATE'], momentum=config['MOMENTUM']) # Used to update the weights of the model

# The neural network
class StockNet(Module):
	def __init__(self, device):
		super(StockNet, self).__init__()

		self.lstm = LSTM(input_size=10, hidden_size=50, num_layers=2, batch_first=True, device=device)
		self.linear = Linear(50, 2, device=device)

	def forward(self, x):
		x, _ = self.lstm(x)
		x = self.linear(x)
		return x

# Create a custom Dataset() class
class StockNetDataset(Dataset):
	def __init__(self, x: Tensor, y: Tensor):
		self.x = x
		self.y = y

	def __len__(self):
		return len(self.y)
	
	def __getitem__(self, index):
		return self.x[index], self.y[index]
	
