import numpy as np
import pandas as pd
import os
import pickle
import logging

import torch
from torchvision import transforms
from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader, random_split

from capstone_project.utils import imshow, save_object, load_object

def load_data(project_dir, data_dir, filename):
    logging.info('Loading "{}"...'.format(filename))
    filename = os.path.join(project_dir, data_dir, filename)
    data = np.load(filename)
    data = data.swapaxes(0,1)
    logging.info('Done.')
    return data

def get_time_buckets_dict(time_buckets):
    '''
    Returns a dict, with the time diff
    as its key and the target class (0-indexed) for it as its value
    '''
    logging.info('Getting time buckets dictionary...')
    bucket_idx = 0
    buckets_dict = {}
    for bucket in time_buckets:
        for time in bucket:
            buckets_dict[time] = bucket_idx
        bucket_idx += 1
    logging.info('Done.')
    return buckets_dict

def get_frame_differences_dict(num_total_frames, max_frame_diff, num_frames_in_stack):
    '''
    Returns a dict with the key as the time difference between the frames
    and the value as a list of tuples (start_frame, end_frame) containing
    all the pair of frames with that diff in time
    '''
    logging.info('Getting frame differences dictionary...')
    differences_dict = {}
    differences = range(max_frame_diff+1)
    for diff in differences:
        start_frame = num_frames_in_stack-1
        end_frame = start_frame+diff
        while end_frame <= num_total_frames-1:
            differences_dict.setdefault(diff, []).append(tuple((start_frame, end_frame)))
            start_frame += 1
            end_frame += 1
    print('Done.')
    return differences_dict

def get_samples_at_difference(data, difference, differences_dict, num_pairs_per_example, num_frames_in_stack, time_buckets_dict):
    '''
    The task of this function is to get the samples by first selecting the list of tuples
    for the associated time difference, and then sampling the num of pairs per video example
    and then finally returning, the video pairs and their associated class(for the time bucket)
    '''
    logging.info('Getting all pairs with a frame difference of {}...'.format(difference))
    video_pairs, y = [], []
    candidates = differences_dict[difference]
    np.random.seed(1337)
    idx_pairs = np.random.choice(len(candidates), size=num_pairs_per_example)
    for row in data:
        for idx_pair in idx_pairs:
            target1_last_frame, target2_last_frame = candidates[idx_pair]
            target1_frames = list(range(target1_last_frame-num_frames_in_stack+1, target1_last_frame+1))
            target2_frames = list(range(target2_last_frame-num_frames_in_stack+1, target2_last_frame+1))
            video_pairs.append([row[target1_frames], row[target2_frames]])
            bucket = time_buckets_dict[difference]
            y.append(bucket)
    logging.info('Done.')
    return np.array(video_pairs), np.array(y)

def get_paired_data(project_dir, data_dir, plots_dir, filename, time_buckets, num_passes_for_generation=2, num_pairs_per_example=1, num_frames_in_stack=2, force=False):
    mean, std = 0, 1
    data = load_data(project_dir, data_dir, filename)
    imshow(data, mean, std, project_dir, plots_dir)

    num_total_frames = data.shape[1]
    max_frame_diff = np.hstack([bucket for bucket in time_buckets]).max()
    assert max_frame_diff <= num_total_frames-num_frames_in_stack, \
        'Cannot have difference of {} when sequence length is {} and number of \
        stacked frames are {}'.format(max_frame_diff, num_total_frames, num_frames_in_stack)

    filename = '.'.join(filename.split('.')[:-1])
    X_path = os.path.join(project_dir, data_dir, '{}_X.pkl'.format(filename))
    y_path = os.path.join(project_dir, data_dir, '{}_y.pkl'.format(filename))
    if not force and os.path.exists(X_path) and os.path.exists(y_path):
        data = None
        logging.info('Found existing data. Loading it...')
        X = load_object(X_path)
        y = load_object(y_path)
        logging.info('Done.')
        return X, y
    logging.info('Did not find existing data. Creating it...')
    time_buckets_dict = get_time_buckets_dict(time_buckets)
    differences_dict = get_frame_differences_dict(num_total_frames, max_frame_diff, num_frames_in_stack)
    X, y = np.array([]), np.array([])
    for i in range(num_passes_for_generation):
        logging.info('Making pass {} through data...'.format(i+1))
        for difference in range(max_frame_diff+1):
            video_pairs, targets = get_samples_at_difference(data, difference, differences_dict, num_pairs_per_example, num_frames_in_stack, time_buckets_dict)
            X = np.vstack((X, video_pairs)) if X.size else video_pairs
            y = np.append(y, targets)
        logging.info('Done.')
    logging.info('Data generation done. Dumping data to disk...')
    save_object(X, X_path)
    save_object(y, y_path)
    logging.info('Done.')
    return X, y

class MovingMNISTDataset(Dataset):
    # TODO: write function for implementing transforms
    def __init__(self, X, y, transforms=None):
        self.X = X
        self.y = y
        self.transforms = transforms

    def __getitem__(self, index):
        # Load data and get label
        x1 = self.X[index][0]
        x2 = self.X[index][1]
        y = self.y[index]
        return x1, x2, y

    def __len__(self):
        return len(self.y)

def generate_dataloader(X, y, test_size, val_size, batch_size, project_dir, plots_dir):
    # TODO: Normalize data
    # mean = np.mean(dataset)
    # std = np.std(dataset)
    # dataset = (dataset - mean)/std
    # data_transform = transforms.Compose([
    #     transforms.ToTensor(),
    #     transforms.Normalize((mean,), (std,))
    # ])
    logging.info('Generating train, val, and test data loaders...')
    X, y = torch.from_numpy(X), torch.from_numpy(y)
    dataset = MovingMNISTDataset(X, y, transforms=None)

    num_test = int(np.floor(test_size*len(dataset)))
    num_train_val = len(dataset) - num_test
    num_val = int(np.floor(num_train_val*val_size/(1 - test_size)))
    num_train = num_train_val - num_val

    train_dataset, val_dataset, test_dataset = random_split(dataset, [num_train, num_val, num_test])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    test_loader  = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

    logging.info('Done.')

    return train_loader, val_loader, test_loader
