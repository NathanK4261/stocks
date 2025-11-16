import modules.ml as ml

import pandas as pd
import numpy as np

import torch
import torch.utils.data

import json

from tqdm import tqdm

# Load config
with open('config.json') as f:
	config = json.load(f)

# Select appropriate backend device
device = (
    'cuda' if torch.cuda.is_available()
    else 'mps' if torch.backends.mps.is_available()
    else 'cpu'
)

print(f'BACKEND: {device}')

# Initialize our model
try:
	# Try and load a previous version
	model = ml.StockNet().to(device)
	model.load_state_dict(torch.load('StockNet/model',weights_only=True))
except:
	print('No StockNet model avaliable to load, skipping...')
	model = ml.StockNet().to(device)

# Initialize our optimizer
try:
	# Try and load a previous version
	optimizer = torch.optim.Adam(model.parameters(), lr=config['LEARNING_RATE'])
	optimizer.load_state_dict(torch.load('StockNet/optimizer',weights_only=True))
except:
	print('No StockNet optimizer avaliable to load, skipping...')
	optimizer = torch.optim.Adam(model.parameters(), lr=config['LEARNING_RATE']) # Used to update the weights of the model

# Initialize our loss function
loss_func = torch.nn.BCEWithLogitsLoss()

# Load training data
stockdata = pd.read_csv('stockdata/training_data.csv')

# Group dataframe by ticker, than create list of datframes for each ticker
stockdata_individual = list(stockdata.groupby('ticker'))

# Format data
for _, data in stockdata_individual:
	# Remove companies with insufficient data
	if len(data) < config['LSTM_WINDOW_SIZE'] + 1:
		stockdata_individual.remove((_, data))

	# Remove last row of every companies data, as it is not usefull
	data.drop(data.tail(1).index, inplace=True)

# Iterate through each company, and format data into one (new) big dataframe
X, y = [], []
for _, company_data in stockdata_individual:
	# Seperate data into input and output
	inp = company_data.drop(columns=['ticker','investmentDecision']).astype('float32').reset_index(drop=True)
	out = company_data['investmentDecision'].astype('float32').reset_index(drop=True)

	# Create sequences of 2-day periods
	for i in range(len(inp) - config['LSTM_WINDOW_SIZE']):

		X.append(inp.iloc[i:(i+config['LSTM_WINDOW_SIZE'])])

		# Add "[[]]" to make the output array 2D
		y.append([ out.iloc[i+config['LSTM_WINDOW_SIZE'] - 1] ])

# Convert input and output lists into numpy arrays
X = np.array(X)
y = np.array(y)

# Split into train/test sets
split_idx = int(len(X) * 0.6)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Convert into dataloaders (for model training)
train_dataloader = torch.utils.data.DataLoader(
	ml.StockNetDataset(
		torch.from_numpy(X_train),
		torch.from_numpy(y_train)
	),

	batch_size=config['BATCH_SIZE'],
	shuffle=True
)

test_dataloader = torch.utils.data.DataLoader(
	ml.StockNetDataset(
		torch.from_numpy(X_test),
		torch.from_numpy(y_test)
	),
	batch_size=config['BATCH_SIZE'],
	shuffle=True
)

# Create variables for some config values
best_training_loss = config['BEST_TRAINING_LOSS']

# Main logic to train the neural network
try:
	for epoch in tqdm(range(config['EPOCHS']), desc='Training Progress', unit='Epochs'):
		# Make sure gradient tracking is on
		model.train()

		# Do a pass over the data
		for inputs, moves in iter(train_dataloader):

			# Assign only the current batch to our device to save on memory
			inputs, moves = inputs.to(device), moves.to(device)

			# Zero your gradients for every batch!
			optimizer.zero_grad()

			# Make predictions for this batch
			outputs = model(inputs)

			# Compute the loss and its gradients
			loss = loss_func(outputs, moves)
			loss.backward()

			# Adjust learning weights
			optimizer.step()

		# Set the model to evaluation mode, disabling dropout and using population
		# statistics for batch normalization.
		model.eval()

		# Disable gradient computation and reduce memory consumption.
		with torch.no_grad():
			vloss = 0

			for vinputs, vmoves in iter(test_dataloader):
				
				# Assign only the current batch to our device to save on memory
				vinputs, vmoves = vinputs.to(device), vmoves.to(device)

				voutputs = model(vinputs)

				vloss += loss_func(voutputs, vmoves)

			# Average validation loss over all epochs
			avg_loss = vloss / len(test_dataloader)

			# Track best performance
			if avg_loss.item() < best_training_loss:
				best_training_loss = avg_loss.item()

				# Save the model's state if its loss execeeds the lowest recorded loss in config
				torch.save(model.state_dict(), f'StockNet/model')

				# Save the optimizer's state as well
				torch.save(optimizer.state_dict(), 'StockNet/optimizer')

		#print(f'EPOCH [{epoch}/{config['EPOCHS']}] * Avg. Loss: {"{:.2f}".format(avg_loss.item())} * Best Loss: {"{:.2f}".format(best_training_loss)}\t')
except KeyboardInterrupt:
	pass
finally:
	# Print improvement
	print(f'Improvement: {round(config['BEST_TRAINING_LOSS'] - best_training_loss, 3)} (Start: {round(config['BEST_TRAINING_LOSS'],3)})')
	
	# Save data to config file
	with open('config.json','w') as f:
		# Save best training loss to config file
		try:
			if best_training_loss > 0.1e-5:
				config['BEST_TRAINING_LOSS'] = best_training_loss
			else:
				config['BEST_TRAINING_LOSS'] = 0.00001
		except Exception as e:
			print('Error while saving data - ', str(type(e)))

		# Write new config to file
		json.dump(config, f, indent = 4)