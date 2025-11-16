import torch

# The neural network
class StockNet(torch.nn.Module):
	'''
	# StockNet

	An LSTM neural network for predicting weather to buy/sell a stock
	'''
	def __init__(self):
		super(StockNet, self).__init__()

		self.lstm = torch.nn.LSTM(input_size=31, hidden_size=30, num_layers=1, batch_first=True)
		self.linear = torch.nn.Linear(
			30, # input dimensions
			1 # output dimension(s)
		)

	def forward(self, x):
		'''
		Method for runinng one "forward pass" of the model
		'''

		# Outputs (out = ALL hidden states) (hs = new hidden state) (cs = new cell state)
		out, _ = self.lstm(x)

		# Get the last output
		last = out[:, -1, :]

		return self.linear(last)

# Create a custom Dataset() class
class StockNetDataset(torch.utils.data.Dataset):
	def __init__(self, x: torch.Tensor, y: torch.Tensor):
		self.x = x
		self.y = y

	def __len__(self):
		return len(self.y)
	
	def __getitem__(self, index):
		return self.x[index], self.y[index]