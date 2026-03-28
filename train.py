import modules.ml
import modules.datamanager

import torch
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
	model = modules.ml.StockNet().to(device)
	model.load_state_dict(torch.load('StockNet/model',weights_only=True))
except:
	print('No StockNet model avaliable to load, skipping...')
	model = modules.ml.StockNet().to(device)

# Initialize our optimizer
try:
	# Try and load a previous version
	optimizer = torch.optim.AdamW(model.parameters(), lr=config['LEARNING_RATE'])
	optimizer.load_state_dict(torch.load('StockNet/optimizer',weights_only=True))
except:
	print('No StockNet optimizer avaliable to load, skipping...')
	optimizer = torch.optim.AdamW(model.parameters(), lr=config['LEARNING_RATE']) # Used to update the weights of the model

# Initialize our loss function
loss_func = torch.nn.HuberLoss()

# Load training data
stock_data_manager = modules.datamanager.StockDataManager()

# Create training and testing dataloaders
train_dataloader, test_dataloader = stock_data_manager.train_test_split(config['LSTM_WINDOW_SIZE'], config['BATCH_SIZE'])

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
			total = 0

			for vinputs, vmoves in iter(test_dataloader):
				
				# Assign only the current batch to our device to save on memory
				vinputs, vmoves = vinputs.to(device), vmoves.to(device)

				# Get outputs
				voutputs = model(vinputs)

				# Compute loss based on the current batch (more accurate)
				batch_loss = loss_func(voutputs, vmoves).item()
				vloss += batch_loss * len(vinputs)
				total += len(vinputs)

			# Average validation loss over all epochs
			avg_loss = vloss / total

			# Track best performance
			if avg_loss < best_training_loss:
				best_training_loss = avg_loss

				# Save the model's state if its loss execeeds the lowest recorded loss in config
				torch.save(model.state_dict(), f'StockNet/model')

				# Save the optimizer's state as well
				torch.save(optimizer.state_dict(), 'StockNet/optimizer')

		#print(f'EPOCH [{epoch}/{config['EPOCHS']}] * Avg. Loss: {"{:.2f}".format(avg_loss)} * Best Loss: {"{:.2f}".format(best_training_loss)}\t')
except KeyboardInterrupt:
	pass
finally:
	# Print improvement
	print(f'Improvement: {round(config['BEST_TRAINING_LOSS'] - best_training_loss, 3)} (Start: {round(config['BEST_TRAINING_LOSS'],3)})')
	
	# Save data to config file
	with open('config.json','w') as f:
		# Save best training loss to config file
		try:
			config['BEST_TRAINING_LOSS'] = best_training_loss
		except Exception as e:
			print('Error while saving data - ', str(type(e)))

		# Write new config to file
		json.dump(config, f, indent = 4)