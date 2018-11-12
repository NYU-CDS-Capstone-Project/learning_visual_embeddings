# DS-GA 1006 Capstone Project and Presentation

# Learning Visual Embeddings
Members:
  - Mihir Rana
  - Kenil Tanna


## Requirements
For ease of setup, we have created a [requirements.yaml](https://github.com/NYU-CDS-Capstone-Project/learning_visual_embeddings/blob/master/requirements.yaml) file which will create a conda environment with the name `capstone_project` and install all dependencies and requirements into that environment. To do this:
  - Install Anaconda and run:
```
conda env create -f requirements.yaml
```
  - Optionally, if you want to run it on a GPU, install CUDA and cuDNN

## Installation
Again, for simplicity, we have created a module with the name `capstone_project` which can be installed directly into pip by running the following command from the main project directory:
```
pip install -e .
```

## Usage
```
usage: main.py [-h] [--project-dir PROJECT_DIR] [--dataset DATASET]
               [--data-ext DATA_EXT] [--data-dir DATA_DIR] [--offline]
               [--checkpoints-dir CHECKPOINTS_DIR]
               [--load-ckpt LOAD_CHECKPOINT] [--batch-size BATCH_SIZE]
               [--epochs EPOCHS] [--device DEVICE] [--device-id DEVICE_ID]
               [--ngpu NGPU] [--parallel] [--lr LR] [--num-train NUM_TRAIN]
               [--num-frames NUM_FRAMES_IN_STACK]
               [--num-pairs NUM_PAIRS_PER_EXAMPLE] [--use-pool] [--use-res]
               [--force]

optional arguments:
  -h, --help                          show this help message and exit
  --project-dir PROJECT_DIR           path to project directory
  --dataset DATASET                   name of dataset file in "data" directory
                                      mnist_test_seq | moving_bars_20_121 | etc., default=mnist_test_seq
  --data-ext DATA_EXT                 extension of dataset file in data directory
  --data-dir DATA_DIR                 path to data directory (used if different from "data")
  --offline                           use offline preprocessing of data loader
  --checkpoints-dir CHECKPOINTS_DIR   path to checkpoints directory (used if different from "checkpoints")
  --load-ckpt LOAD_CHECKPOINT         name of checkpoint file to load
  --batch-size BATCH_SIZE             input batch size, default=64
  --epochs EPOCHS                     number of epochs, default=10
  --lr LR                             learning rate, default=1e-4
  --device                            cuda | cpu, default=cuda
                                      device to train on
  --device-id DEVICE_ID               device id of gpu, default=0
  --ngpu NGPU                         number of GPUs to use (0,1,...,ngpu-1)
  --parallel                          use all GPUs available
  --num-train NUM_TRAIN               number of training examples
  --num-frames NUM_FRAMES_IN_STACK    number of stacked frames, default=2
  --num-pairs NUM_PAIRS_PER_EXAMPLE   number of pairs per video, default=5
  --use-pool                          use max pooling instead of strided convolutions
  --use-res                           use residual layers
  --force                             overwrites all existing dumped data sets (if used with `--offline`)
```
