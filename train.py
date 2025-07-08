import pandas as pd

from modules.ml import *

import torch
from torch.utils.data import DataLoader

import json
with open('config.json') as f:
	config = json.load(f)

# Select appropriate backend device
device = (
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)

print(f"BACKEND: {device}")

# Load our ML tools
tools = MLTools(device=device)

# Load our dataframe
df = pd.read_pickle(f'stockdata/{config['TICKER']}/{config['TICKER']}.pkl')

# Create our independent/dependent features
X=df.drop(['date','move'],axis=1).values
Y = df['move'].values.astype(float)

# Split the data into train and test sets
X_train, X_val, Y_train, Y_val = tools.load_training_dataset(X,Y)

# Create dataloaders for training and testing
train_dataloader = DataLoader(StockNetDataset(X_train, Y_train), batch_size=config['BATCH_SIZE'],shuffle=True)
validation_dataloader = DataLoader(StockNetDataset(X_val, Y_val), batch_size=config['BATCH_SIZE'],shuffle=False)

# Initialize our model
model = tools.model

# Initialize our loss function and optimizer
loss_function = tools.loss_function
optimizer = tools.optimizer

# Float to compare average losses to the best loss recorded in config
starting_best_training_loss = config['BEST_TRAINING_LOSS']

# Float that will be updated and saved to config after training
best_training_loss = config['BEST_TRAINING_LOSS']

# Report which ticker is being used to train on
print(f'Training on: {config['TICKER']}')

# Report epochs and batch size
print(f'Epochs: {config['EPOCHS']}')
print(f'Batch size: {config['BATCH_SIZE']}')

# Function that trains one epoch given the batch size
def train_epoch():
	for data in iter(train_dataloader):
		# Every data instance is an input + move pair
		inputs, moves = data

		# Zero your gradients for every batch!
		optimizer.zero_grad()

		# Make predictions for this batch
		outputs = model(inputs)

		# Compute the loss and its gradients
		loss = loss_function(outputs, moves)
		loss.backward()

		# Adjust learning weights
		optimizer.step()

# Main logic to train the neural network
try:
	for epoch in range(config['EPOCHS']):
		# Make sure gradient tracking is on
		model.train()

		# Do a pass over the data
		train_epoch()

		# Set the model to evaluation mode, disabling dropout and using population
		# statistics for batch normalization.
		model.eval()

		# Disable gradient computation and reduce memory consumption.
		with torch.no_grad():
			vloss = 0

			for i, vdata in enumerate(validation_dataloader):
				vinputs, vmoves = vdata # Get inputs and moves from validation data

				voutputs = model(vinputs)

				vloss += loss_function(voutputs, vmoves)

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
		if best_training_loss > 0.1e-5:
			config['BEST_TRAINING_LOSS'] = best_training_loss
		else:
			config['BEST_TRAINING_LOSS'] = 0.00001

		# Write new config to file
		json.dump(config, f, indent = 4)