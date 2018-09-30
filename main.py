import numpy as np
import pandas as pd
import os
import argparse

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable
from torch.utils.data.sampler import Sampler

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from torchviz import make_dot, make_dot_from_trace

from capstone_project.preprocessing import get_paired_data, generate_dataloader
from capstone_project.models.embedding_network import EmbeddingNetwork
from capstone_project.models.classification_network import ClassificationNetwork
from capstone_project.utils import train, test, accuracy, save_plot


parser = argparse.ArgumentParser()
parser.add_argument('--project-dir', metavar='project_dir', dest='project_dir', help='path to project directory', required=False)
parser.add_argument('--dataset', metavar='dataset', dest='dataset', help='name of dataset file in data directory', required=False)
parser.add_argument('--batch-size', metavar='batch_size', dest='batch_size', help='batch size', required=False, default=16)
parser.add_argument('--epochs', metavar='epochs', dest='epochs', help='number of epochs', required=False, default=50)
parser.add_argument('--device', metavar='device', dest='device', help='device', required=False)
parser.add_argument('--lr', metavar='lr', dest='lr', help='learning rate', required=False, default=0.01)
args = parser.parse_args()


# Globals
PROJECT_DIR = args.project_dir if args.project_dir else '/home/mihir/Desktop/GitHub/nyu/capstone_project/'
DATA_DIR, PLOTS_DIR = 'data', 'plots'
DATASET = args.dataset if args.dataset else 'mnist_test_seq.npy'
NUM_ROWS = 1
TEST_SIZE, VAL_SIZE = 0.2, 0.2
BATCH_SIZE = args.batch_size     # input batch size for training
N_EPOCHS = args.epochs    # number of epochs to train
LR = args.lr           # learning rate
DEVICE = args.device if args.device else 'cuda' if torch.cuda.is_available() else 'cpu'
NUM_FRAMES_IN_STACK = 1
NUM_VIDEOS_PER_ROW = 1
TIME_BUCKETS = [[0], [1], [2], [3,4], list(range(5,11,1)), list(range(11,20,1))]

def main():
    X, y = get_paired_data(PROJECT_DIR, DATA_DIR, PLOTS_DIR, DATASET, TIME_BUCKETS, NUM_ROWS, NUM_VIDEOS_PER_ROW, force=False)
    train_loader, val_loader, test_loader = generate_dataloader(X, y, TEST_SIZE, VAL_SIZE, BATCH_SIZE, PROJECT_DIR, PLOTS_DIR)

    if DATASET == 'mnist_test_seq.npy':
        in_dim, in_channels, out_dim = 64, 1, 1024
        embedding_hidden_size, classification_hidden_size = 1024, 1024
        num_outputs = 6
    elif DATASET == 'cifar10':
        in_dim, in_channels, out_dim = 32, 3, 1024
        embedding_hidden_size, classification_hidden_size = 1024, 1024
        num_outputs = 10

    train_loss_history = []
    test_loss_history = []
    embedding_network = EmbeddingNetwork(in_dim, in_channels, out_dim, embedding_hidden_size).to(DEVICE)
    classification_network = ClassificationNetwork(out_dim, num_outputs, classification_hidden_size).to(DEVICE)

    criterion_train = nn.CrossEntropyLoss()
    criterion_test = nn.CrossEntropyLoss(reduction='sum')
    optimizer = optim.SGD(list(embedding_network.parameters()) + list(classification_network.parameters()), lr=LR)

    for epoch in range(1, N_EPOCHS+1):
        train_loss = train(
            embedding_network=embedding_network,
            classification_network=classification_network,
            criterion=criterion_train,
            dataloader=train_loader,
            optimizer=optimizer,
            device=DEVICE,
            epoch=epoch
        )

        test_loss, test_pred, test_true = test(
            embedding_network=embedding_network,
            classification_network=classification_network,
            dataloader=test_loader,
            criterion=criterion_test,
            device=DEVICE
        )

        accuracy_train = accuracy(embedding_network, classification_network, train_loader, criterion_test, DEVICE)
        accuracy_test = accuracy(embedding_network, classification_network, test_loader, criterion_test, DEVICE)
        train_loss_history.append(train_loss)
        test_loss_history.append(test_loss)

        print('TRAIN Epoch: {}\tAverage loss: {:.4f}, Accuracy: {:.0f}%'.format(epoch, train_loss, accuracy_train))
        print('TEST  Epoch: {}\tAverage loss: {:.4f}, Accuracy: {:.0f}%\n'.format(epoch, test_loss, accuracy_test))

    loss_history_df = pd.DataFrame({
        'train': train_loss_history,
        'test': test_loss_history,
    })

    fig = plt.figure()
    loss_history_df.plot(alpha=0.5, figsize=(10,8))
    save_plot(PROJECT_DIR, PLOTS_DIR, fig, 'loss_vs_iterations.png')

    total_parameters_dict = dict(embedding_network.named_parameters())
    total_parameters_dict.update(dict(classification_network.named_parameters()))
    embedding_output1 = embedding_network(train_loader.dataset[0][0].view(-1, 1, 64, 64).to(DEVICE).float())
    embedding_output2 = embedding_network(train_loader.dataset[1][0].view(-1, 1, 64, 64).to(DEVICE).float())
    classification_input = torch.dot(embedding_output1, embedding_output2)
    classification_output = classification_network(classification_input)
    make_dot(classification_output, params=total_parameters_dict)

    with torch.onnx.set_training(network, False):
        embedding_output1 = embedding_network(train_loader.dataset[0][0].view(-1, 1, 64, 64).to(DEVICE).float())
        embedding_output2 = embedding_network(train_loader.dataset[1][0].view(-1, 1, 64, 64).to(DEVICE).float())
        classification_input = torch.dot(embedding_output1, embedding_output2)
        trace, _ = torch.jit.get_trace_graph(classification_network, args=(classification_input,))
    make_dot_from_trace(trace)

if __name__ == '__main__':
    main()
