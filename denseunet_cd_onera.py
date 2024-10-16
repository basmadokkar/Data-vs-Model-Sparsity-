# -*- coding: utf-8 -*-
"""DenseUNet CD ONERA.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1JUlfE2WX__O1ITTxxvOIgnCQiCizZS1h
"""

import random
import numpy as np
from matplotlib import pyplot as plt
import tifffile as tiff
import glob
import os
import cv2
import tensorflow as tf
from tensorflow.python.client import device_lib
from sklearn.model_selection import train_test_split
import tensorflow as tf
from keras.models import Model
from keras.applications import DenseNet121
from keras.layers import Input,Dense,Reshape,Flatten,Input,GlobalAveragePooling2D,Conv2D,MaxPool2D,BatchNormalization,Conv2DTranspose,concatenate,UpSampling2D
from keras import optimizers
from keras.optimizers import Adam
from keras.metrics import MeanIoU
from keras import backend as K
from sklearn import metrics
from google.colab import drive

from keras.preprocessing.image import ImageDataGenerator
from skimage.filters import threshold_otsu, threshold_multiotsu
from cv2 import adaptiveThreshold
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import warnings

from keras.models import Model
from keras.layers import Dropout, Activation, Reshape

from keras.layers import Conv2D, Conv2DTranspose,UpSampling2D
from keras.layers import AveragePooling2D
#from keras.layers import merge
from keras.layers import BatchNormalization
from keras.regularizers import l2
from keras.utils import get_source_inputs
# from keras_applications.imagenet_utils import _obtain_input_shape
import keras.backend as K

import tensorflow as tf




def FocalTverskyLoss(targets, inputs, alpha=0.7, gamma=0.75, smooth=1e-6):
    # Flatten label and prediction tensors
    inputs = tf.reshape(inputs, [-1])
    targets = tf.reshape(targets, [-1])

    # True Positives, False Positives & False Negatives
    TP = tf.reduce_sum(inputs * targets)
    FP = tf.reduce_sum((1 - targets) * inputs)
    FN = tf.reduce_sum(targets * (1 - inputs))

    Tversky = (TP + smooth) / (TP + alpha * FP + (1 - alpha) * FN + smooth)
    FocalTversky = tf.pow((1 - Tversky), gamma)

    return FocalTversky

phisycal_devices = tf.config.experimental.list_physical_devices('GPU')
print("Num of GPUs available: ",len(phisycal_devices))



from tensorflow.keras.layers import Conv2D, BatchNormalization, Activation, MaxPool2D, Conv2DTranspose, Concatenate, Input
from tensorflow.keras.models import Model
from tensorflow.keras.applications import DenseNet121

def conv_block(inputs, num_filters):
    x = Conv2D(num_filters, 3, padding="same")(inputs)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    x = Conv2D(num_filters, 3, padding="same")(x)
    x = BatchNormalization()(x)
    x = Activation("relu")(x)

    return x

def decoder_block(inputs, skip_features, num_filters):
    x = Conv2DTranspose(num_filters, (2, 2), strides=2, padding="same")(inputs)
    x = Concatenate()([x, skip_features])
    x = conv_block(x, num_filters)
    return x



def build_densenet121_unet(input_shape):
    """ Input """
    inputs = Input(input_shape, name="input_1")

    """ Pre-trained DenseNet121 Model """
    densenet = DenseNet121(include_top=False, weights=None, input_tensor=inputs)

    """ Encoder """

    s1 = densenet.get_layer("input_1").output       ## 512
    s2 = densenet.get_layer("conv1/relu").output    ## 256
    s3 = densenet.get_layer("pool2_relu").output ## 128
    s4 = densenet.get_layer("pool3_relu").output  ## 64

    """ Bridge """
    b1 = densenet.get_layer("pool4_relu").output  ## 32

    """ Decoder """
    d1 = decoder_block(b1, s4, 256)             ## 64
    d2 = decoder_block(d1, s3, 128)             ## 128
    d3 = decoder_block(d2, s2, 64)             ## 256
    d4 = decoder_block(d3, s1, 32)              ## 512

    """ Outputs """
    outputs = Conv2D(1, 1, padding="same", activation="sigmoid")(d4)

    model = Model(inputs, outputs)
    return model




if __name__ == "__main__":
    input_shape = (256, 256, 3)
    model = build_densenet121_unet(input_shape)
    model.summary()



image_number = random.randint(0, len(X_train))
print(image_number)
plt.figure(figsize=(12, 6))
plt.subplot(121)
plt.imshow(np.reshape(X_train[image_number], (256, 256,3)), cmap='gray')
plt.subplot(122)
plt.imshow(np.reshape(y_train[image_number], (256, 256)), cmap='gray')
plt.show()

# Commented out IPython magic to ensure Python compatibility.
# %%time
# seed=24
# 
# img_data_gen_args = dict(rotation_range=90,
#                      width_shift_range=0.3,
#                      height_shift_range=0.3,
#                      horizontal_flip=True,
#                      vertical_flip=True,
#                      shear_range=0.5,
#                      fill_mode='reflect')
# 
# mask_data_gen_args = dict(rotation_range=90,
#                      width_shift_range=0.3,
#                      height_shift_range=0.3,
#                      horizontal_flip=True,
#                      vertical_flip=True,
#                      shear_range=0.5,
#                      fill_mode='reflect') #Binarize the output again.
# 
# X_train=X_train.reshape(582, 256, 256, 3)
# X_test=X_test.reshape(195, 256, 256, 3)
# image_data_generator = ImageDataGenerator(**img_data_gen_args)
# image_data_generator.fit(X_train, augment=True, seed=seed)
# image_generator = image_data_generator.flow(X_train, seed=seed)
# valid_img_generator = image_data_generator.flow(X_test, seed=seed)

# Commented out IPython magic to ensure Python compatibility.
# %%time
# 
# mask_data_generator = ImageDataGenerator(**mask_data_gen_args)
# mask_data_generator.fit(y_train, augment=True, seed=seed)
# mask_generator = mask_data_generator.flow(y_train, seed=seed)
# valid_mask_generator = mask_data_generator.flow(y_test, seed=seed)

def my_image_mask_generator(image_generator, mask_generator):
    train_generator = zip(image_generator, mask_generator)
    for (img, mask) in train_generator:
        yield (img, mask)

my_generator = my_image_mask_generator(image_generator, mask_generator)

validation_datagen = my_image_mask_generator(valid_img_generator, valid_mask_generator)

x = image_generator.next()
y = mask_generator.next()
for i in range(0,1):
    image = x[i]
    mask = y[i]
    plt.subplot(1,2,1)
    plt.imshow(image[:,:,0], cmap='gray')
    plt.subplot(1,2,2)
    plt.imshow(mask[:,:,0])
    plt.show()



# Commented out IPython magic to ensure Python compatibility.
# %%time
# # model = get_model()
# from tensorflow import keras
# #@title Select parameters {run: "auto"}
# 
# optimizer = 'adam' #@param ["adam" , "momentum" , "rmsprop" , "adagrad", "nag"] {type :"string"}
# Learning_rate = 0.001 #@param {type:"number"}
# LR = float(Learning_rate)
# if (optimizer=="adagrad"):
#   opt = keras.optimizers.Adagrad(learning_rate=LR)
# if (optimizer=="adam"):
#   opt = keras.optimizers.Adam(learning_rate=LR)
# if (optimizer=="RMSprop"):
#   opt = keras.optimizers.RMSProp(learning_rate=LR)
# if (optimizer=="momentum"):
#   opt = keras.optimizers.SGD(learning_rate=LR,momentum=0.9)
# if (optimizer=="nag"):
#   opt = keras.optimizers.SGD(learning_rate=LR,momentum=0.9,nesterov=True)
# 
# batch_size = 64
# steps_per_epoch = 3*(len(X_train))//batch_size
# model.compile(optimizer= opt, loss=FocalTverskyLoss, metrics=['acc'])
# callback = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=10)
# history = model.fit(my_generator,
#                     validation_data = validation_datagen,
#                     steps_per_epoch = steps_per_epoch,
#                     validation_steps = steps_per_epoch,
#                     callbacks= callback,
#                     epochs=200)

#plot the training and validation accuracy and loss at each epoch
# batch_size*steps_per_epoch*len(loss)
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

acc = history.history['acc']
val_acc = history.history['val_acc']

plt.plot(epochs, acc, 'y', label='Training acc')
plt.plot(epochs, val_acc, 'r', label='Validation acc')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

test_img_number = random.randint(0, len(X_test))
test_img = X_test[test_img_number]
ground_truth=y_test[test_img_number]
# test_img_norm=test_img[:,:,0][:,:,None]
test_img_input=np.expand_dims(test_img, 0)
print(test_img_number)
prediction = model.predict(test_img_input)
prediction = prediction> threshold_otsu(prediction)
prediction=prediction[0,:,:,0]
plt.figure(figsize=(16, 8))
plt.subplot(231)
plt.title('Testing Image')
plt.imshow(test_img[:,:,0], cmap='gray')
plt.subplot(232)
plt.title('Testing Label')
plt.imshow(ground_truth[:,:,0], cmap='gray')
plt.subplot(233)
plt.title('Prediction on test image')
plt.imshow(prediction, cmap='gray')
plt.show()

