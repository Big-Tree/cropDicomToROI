import pickle
import matplotlib.pyplot as plt
import numpy as np


# Load in the pickle file and view some of the files, print out info
def load_pickle(path):
    return pickle.load(open(path, 'rb'))


# Copy and paste the colour channel (X, Y, 1) -> (X, Y, 3)
def expand_channels(img):
    tmp = np.concatenate((img,img,img), axis = 2)
    return tmp


def print_images():
    blob = load_pickle(
        '/vol/research/mammo2/will/data/batches/roi/batches_1-7.pickle')
    print('len(blob): ', len(blob))

    # Display the first image
    img = blob[next(iter(blob))]
    # Window between the percentiles and normalise between 0-1
    p_down = np.percentile(img,0)
    p_up = np.percentile(img,100)
    img = (img-p_down) / (p_up - p_down)
    print('img.shape: ', img.shape)
    img = expand_channels(img)
    print('img.shape: ', img.shape)
    print('\n\n', img)
    plt.imshow(img)
    plt.show()


def main():
    print_images()


if __name__ == '__main__':
    main()

