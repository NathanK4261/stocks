import modules.ml as ml

import pandas as pd
import numpy as np

import torch
import torch.utils.data

import json

# Load config
with open('config.json') as f:
	config = json.load(f)

# Create variables for some config values
best_training_loss = config['BEST_TRAINING_LOSS']

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

for data in stockdata_individual:

	# Remove companies with insufficient data
	if len(data[1]) < 3:
		stockdata_individual.remove(data)

	# Remove last row of every companies data, as it is not usefull
	data[1].drop(data[1].index[-1])

# Initialize hidden and cell states
hidden_state, cell_state = None, None

# Iterate through each company, and format data into input and output lists
X, y = [], []
for company_data in stockdata_individual:

	# Seperate data into input and output
	inp = company_data[1].drop(columns=['ticker','investmentDecision']).astype('float32').reset_index(drop=True)
	out = company_data[1]['investmentDecision'].astype('float32').reset_index(drop=True)

	# Create sequences of 2-day periods
	for i in range(len(inp) - 2):
		X.append(inp.iloc[i:(i+2)])
		y.append(out.iloc[i+1])

# Convert input and output lists into numpy arrays
X = np.array(X)
y = np.array(y)

# Split into train/test sets (still keep chronological order)
split_idx = int(len(X) * 0.6)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Convert into dataloaders (for model training)
train_dataloader = torch.utils.data.DataLoader(
	ml.StockNetDataset(
		torch.from_numpy(X_train).to(device),
		torch.from_numpy(y_train).to(device)
	),

	batch_size=config['BATCH_SIZE'],
	shuffle=True
)

test_dataloader = torch.utils.data.DataLoader(
	ml.StockNetDataset(
		torch.from_numpy(X_test).to(device),
		torch.from_numpy(y_test).to(device)
	),
	batch_size=config['BATCH_SIZE'],
	shuffle=True
)

# Main logic to train the neural network
try:
	for epoch in range(config['EPOCHS']):
		# Make sure gradient tracking is on
		model.train()

		# Do a pass over the data
		for data in iter(train_dataloader):
			# Every data instance is an input + move pair
			inputs, move = data

			# Zero your gradients for every batch!
			optimizer.zero_grad()

			# Make predictions for this batch
			outputs, hidden_state, cell_state = model(inputs, hidden_state, cell_state)

			# Compute the loss and its gradients
			loss = loss_func(outputs, move)
			loss.backward()

			# Adjust learning weights
			optimizer.step()

			# Detatch hidden and cell state to avoid gradient buildup
			hidden_state, cell_state = hidden_state.detach(), cell_state.detach()

		# Set the model to evaluation mode, disabling dropout and using population
		# statistics for batch normalization.
		model.eval()

		# Disable gradient computation and reduce memory consumption.
		with torch.no_grad():
			i = 0
			vloss = 0

			for _, vdata in enumerate(test_dataloader):
				vinputs, vmoves = vdata # Get inputs and moves from validation data

				voutputs, _, _ = model(vinputs)

				vloss += loss_func(voutputs, vmoves)

				i+=1

			# Average validation loss over all epochs
			avg_loss = vloss / (i + 1)

			# Track best performance
			if avg_loss.item() < best_training_loss:
				best_training_loss = avg_loss.item()

				# Save the model's state if its loss execeeds the lowest recorded loss in config
				torch.save(model.state_dict(), f'StockNet/model')

				# Save the optimizer's state as well
				torch.save(optimizer.state_dict(), 'StockNet/optimizer')

		# Print training progress
		progress = round(epoch / config['EPOCHS'],2)
		print(f' Epoch: {epoch}/{config['EPOCHS']} ({int(100*progress)}%){' '*10}Avg. Loss: {round(avg_loss.item(),3)}{' '*10}Best Loss: {round(best_training_loss,3)}    ',end='\r')
		
except KeyboardInterrupt:
	pass
finally:
	# Print improvement
	print(' '*100,end='\r')
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