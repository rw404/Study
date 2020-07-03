import sys, numpy as np
from keras.datasets import mnist

np.random.seed(1)

(x_train, y_train), (x_test, y_test) = mnist.load_data()

images = x_train[0:1000].reshape(1000, 28*28) / 255
labels = y_train[0:1000]

one_hot_labels = np.zeros((len(labels), 10))
for i, l in enumerate(labels):
    one_hot_labels[i][l] = 1
labels = one_hot_labels

test_images = x_test.reshape(len(x_test), 28*28) / 255
test_labels = np.zeros((len(y_test), 10))
for i, l in enumerate(y_test):
    test_labels[i][l] = 1

def tanh(x):
    return np.tanh(x)
def tanh2deriv(output):
    return 1 - (output ** 2)
def softmax(x):
    temp = np.exp(x)
    return temp/np.sum(temp, axis = 1, keepdims=True)

batch_size = 128

alpha, iterations, pixels_per_image, num_labels = (2, 300, 784, 10)

#CNN
input_rows = 28
input_cols = 28

kernel_rows = 3
kernel_cols = 3
num_kernels = 16

hidden_size = ((input_rows - kernel_rows) * (input_cols - kernel_cols)) * num_kernels

kernels = 0.02 * np.random.random((kernel_rows*kernel_cols, num_kernels)) - 0.01 
weights_1_2 = 0.2 * np.random.random((hidden_size, num_labels)) - 0.1

def get_image_section(layer, row_from, row_to, col_from, col_to):
    section = layer[:, row_from: row_to, col_from: col_to]
    return section.reshape(-1, 1, row_to - row_from, col_to - col_from)

#structure of neural network:
#layer_0 - matrix 100x28x28
# ||
# \/
#flattened_input - matrix 128*25*25 x 9
#kernels - matrix 9x16
#layer_1 - matrix 128*25*25x16(16 - num_kernels)
# ||
# \/
#layer_1 - matrix 128 x 25*25*16
#weights_1_2 - matrix 25*25*16x10
#layer_2 - matrix 128x10 - output

for j in range(iterations):
    correct_cnt = 0

    for i in range(int(len(images)/batch_size)):
        batch_start = i*batch_size
        batch_end = batch_start + batch_size
        layer_0 = images[batch_start:batch_end]    
        layer_0 = layer_0.reshape(layer_0.shape[0], 28, 28)
        
        sects = list()
        for row_start in range(layer_0.shape[1] - kernel_rows):
            for col_start in range(layer_0.shape[2] - kernel_cols):
                sect = get_image_section(layer_0, row_start, row_start+kernel_rows, col_start, col_start+kernel_cols)
                sects.append(sect)

        expanded_input = np.concatenate(sects, axis = 1)
        es = expanded_input.shape
        flattened_input = expanded_input.reshape(es[0]*es[1], -1)

        kernel_output = flattened_input.dot(kernels)

        layer_1 = tanh(kernel_output.reshape(es[0], -1))
        dropout_mask = np.random.randint(2, size = layer_1.shape)
        layer_1 *= dropout_mask * 2 
        layer_2 = softmax(np.dot(layer_1, weights_1_2))
        
        for k in range(batch_size):
            correct_cnt += int(np.argmax(layer_2[k:k+1]) == np.argmax(labels[batch_start+k:batch_start+k+1]))

        layer_2_delta = (labels[batch_start:batch_end] - layer_2)/(batch_size*layer_2.shape[0])
        layer_1_delta = layer_2_delta.dot(weights_1_2.T) * tanh2deriv(layer_1)
        
        layer_1_delta *= dropout_mask

        weights_1_2 += alpha * layer_1.T.dot(layer_2_delta)
        
        l1d_reshape = layer_1_delta.reshape(kernel_output.shape)
        k_update = flattened_input.T.dot(l1d_reshape)
        kernels += alpha * k_update
    
    test_correct_cnt = 0

    for i in range(len(test_images)):
        layer_0 = test_images[i:i+1]    
        layer_0 = layer_0.reshape(layer_0.shape[0], 28, 28)

        sects = list()
        for row_start in range(layer_0.shape[1] - kernel_rows):
            for col_start in range(layer_0.shape[2] - kernel_cols):
                sect = get_image_section(layer_0, row_start, row_start+kernel_rows, col_start, col_start+kernel_cols)
                sects.append(sect)

        expanded_input = np.concatenate(sects, axis = 1)
        es = expanded_input.shape
        flattened_input = expanded_input.reshape(es[0]*es[1], -1)

        kernel_output = flattened_input.dot(kernels)

        layer_1 = tanh(kernel_output.reshape(es[0], -1))
        layer_2 = np.dot(layer_1, weights_1_2)         
        test_correct_cnt += int(np.argmax(test_labels[i:i+1]) == np.argmax(layer_2))
   
    if(j%1 == 0):
        sys.stdout.write("\n" + "I:"+str(j) + " Test-correct:" + str(test_correct_cnt/float(len(test_images))) + " Correct:" + str(correct_cnt/float(len(images))))

