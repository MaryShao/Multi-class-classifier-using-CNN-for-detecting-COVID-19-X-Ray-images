# -*- coding: utf-8 -*-
"""Copy of Covid_reg.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1olLlUqwzJQOZAQz6TbZMXuUlP6mBq4f8
"""

# Commented out IPython magic to ensure Python compatibility.
#coding:utf-8
# %tensorflow_version 2.x
import tensorflow as tf
device_name = tf.test.gpu_device_name()
from keras import regularizers
import seaborn as sns
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
import string
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import os
import sys  
sys.path.append('../')

from sklearn.metrics import confusion_matrix
from sklearn.metrics import plot_confusion_matrix
from keras.utils.np_utils import to_categorical

from keras.layers import(
	Input,
	Activation,
	merge,
	Dense,
	Reshape,
	Flatten,
	advanced_activations,
	TimeDistributed
)
from keras.layers.core import Dropout
from keras.layers.core import RepeatVector
from keras.layers import Multiply
#from keras.layers.recurrent import CNN
#from keras.layers import CNN
from keras.models import Sequential
from keras.layers.pooling import MaxPooling2D
from keras.layers.convolutional import Convolution2D
from keras.layers.convolutional import Convolution3D
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import Conv3D
from keras.layers.pooling import MaxPooling3D
from keras.layers.pooling import AveragePooling3D
from keras.layers.pooling import GlobalAveragePooling2D
from keras.layers.normalization import BatchNormalization
from keras.optimizers import SGD, Adam
from keras.models import Model
from keras.utils import plot_model
from keras.engine.topology import Layer
from keras import backend as K
from keras.layers.core import Permute
from keras.layers import Dense,Dropout,Flatten,Conv2D,MaxPool2D,Conv1D
from keras.initializers import glorot_uniform
from keras.regularizers import l2
from keras import layers, optimizers, models
from keras.applications.resnet50 import ResNet50
from keras.applications.inception_v3 import InceptionV3
from keras.layers import * 
from keras.callbacks import Callback
from keras.callbacks import EarlyStopping, ModelCheckpoint,ReduceLROnPlateau
import time

import warnings
import argparse
import datetime
import h5py
warnings.filterwarnings("ignore")

# load data
def load_train_images(dirname_src,img_size):
    normal_num = 0
    viral_num = 0
    bacterial_num = 0
    covid_num = 0
    y_train_temp = {}
    with open('train.txt','r') as f:
        content = f.read().splitlines()
    for i in content:
        key = i.split(',')[1].split('/')[1]
        if i.split(',')[2] == 'normal':
            value = 0
            normal_num = normal_num + 1
        elif i.split(',')[2] == 'viral':
            value = 1
            viral_num = viral_num + 1
        elif i.split(',')[2] == 'bacterial':
            value = 2
            bacterial_num = bacterial_num + 1
        elif i.split(',')[2] == 'covid':
            value = 3
            covid_num = covid_num + 1
        else:
            value = 4
        y_train_temp[key] = value  
    division_list = [int(normal_num/10*7),int(viral_num/10*7),int(bacterial_num/10*7),int(covid_num/10*7)]
    
    already = [0,0,0,0]
    for home,dirs,files in os.walk(dirname_src):
        for filename in files:
            filenames = filename.split('.')
            if filenames[1] == 'jpeg':
                y = y_train_temp[filename]
                if already[y] <= division_list[y]:
                  already[y] = already[y] + 1
                  dirname_dst = './train_dataset'
                else:
                  dirname_dst = 'test_dataset'
                if (os.path.exists(dirname_dst) == False):
                  os.makedirs(dirname_dst)
                  print("mkdir path:",dirname_dst)
                dirname_dst_categories = dirname_dst+'/'+str(y)
                if (os.path.exists(dirname_dst_categories) == False):
                  os.makedirs(dirname_dst_categories)
                  print("mkdir path:",dirname_dst_categories)
                filename_src = dirname_src+'/'+filename
                filename_dst = dirname_dst_categories+'/'+filename
                img = Image.open(filename_src)
                img = img.resize((img_size,img_size),Image.LANCZOS)
                img.save(filename_dst)
            #print(filename)

load_train_images("drive/My Drive/4771-sp20-covid/train/train",256)

#!rm -rf train_dataset

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))


def resnet50():
    K.set_learning_phase(0)
    Inp = Input((256, 256, 3))
    base_model = ResNet50(weights='imagenet', include_top=False,input_shape=(256, 256, 3), )
    K.set_learning_phase(1)
    x = base_model(Inp)
    x = GlobalAveragePooling2D(name='average_pool')(x)
    x = Dropout(rate=0.5)(x)
    '''
    x = Flatten(name='flatten')(x)
    x = Dense(1024, activation='relu', kernel_regularizer=regularizers.l2(0.0001), )(x)
    x = BatchNormalization()(x)
    x = Dense(512, activation='relu', kernel_regularizer=regularizers.l2(0.0001))(x)
    x = BatchNormalization(name='bn_fc_01')(x)
    '''
    predictions = Dense(4, activation='softmax')(x)
    model = Model(inputs=Inp, outputs=predictions)

    #for layer in base_model.layers:
        #layer.trainable = False
 
    adam = Adam(lr=0.0005)
    model.compile(loss='categorical_crossentropy',optimizer=adam,metrics = ['accuracy',f1_m,precision_m, recall_m])
    
    return model

def incptv3():
    K.set_learning_phase(0)
    # create the base pre-trained model
    Inp = Input((256, 256, 3))
    base_model = InceptionV3(weights='imagenet', include_top=False, input_shape=(256,256,3))
    K.set_learning_phase(1)
    
    x = base_model(Inp)
    # add a global spatial average pooling layer
    x = GlobalAveragePooling2D()(x)
    # let's add a fully-connected layer
    x = Dense(1024, activation='relu')(x)
    x = Dropout(rate=0.5)(x)
    # and a logistic layer -- let's say we have 200 classes
    predictions = Dense(4, activation='softmax')(x)
 
    # this is the model we will train
    model = Model(inputs=Inp, outputs=predictions)
 
    # first: train only the top layers (which were randomly initialized)
    # i.e. freeze all convolutional InceptionV3 layers
    for layer in base_model.layers:
        layer.trainable = False
 
    # compile the model (should be done *after* setting layers to non-trainable)
    model.compile(optimizer='rmsprop', loss='categorical_crossentropy',metrics = ['accuracy',f1_m,precision_m, recall_m])
    
    return model

def onw_CNN():
    input_shape=(256,256,3)
    batch_size = 32
    v_batch_size = 32
    SEED = 1234
    np.random.seed(SEED)
    random.seed(SEED)

    model = Sequential()

    model.add(Conv2D(16, (3, 3), input_shape=input_shape, kernel_initializer=glorot_uniform(seed=SEED)))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(MaxPooling2D((2, 2)))

    model.add(Conv2D(32, (3, 3), kernel_regularizer=l2(0.01), kernel_initializer=glorot_uniform(seed=SEED)))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(MaxPooling2D((2, 2)))

    model.add(Conv2D(64, (3, 3), kernel_regularizer=l2(0.01), kernel_initializer=glorot_uniform(seed=SEED)))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(MaxPooling2D((2, 2)))
    model.add(Dropout(rate=0.3, seed=SEED))

    model.add(Flatten())
    model.add(Dense(512, kernel_regularizer=l2(0.01), kernel_initializer=glorot_uniform(seed=SEED)))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dense(4, activation='softmax', kernel_initializer=glorot_uniform(seed=SEED)))

    model.compile(optimizer=SGD(lr=0.01, nesterov=True),
                  loss='categorical_crossentropy',
                  metrics=['accuracy',f1_m,precision_m, recall_m])

    ### Details of the model ###
    print(model.summary())
    
    return model

def EvaluateSinglePrecision(real,predict):
	true = 0
	for i in range(len(real)):
		if np.argmax(real[i]) == np.argmax(predict[i]):
			true = true + 1
	#print(true)
	return float(true)/float(len(real))

class LossHistory(Callback):
    def on_train_begin(self, logs={}):
        self.losses = []

    def on_epoch_end(self, batch, logs={}):
        self.losses.append(logs.get('loss'))



class TrainModel(object):

    def __init__(self,data_path,lr,batch_size,nb_end_epoch,nb_start_epoch=0):
        self.data_path = data_path
        self.batch_size = batch_size
        self.lr = lr
        self.nb_start_epoch = nb_start_epoch # 
        self.nb_end_epoch = nb_end_epoch

    def train_ResNet50(self,X,Y,x_test,y_test):

        model = resnet50()
        #model = incptv3()
        #model = onw_CNN()
        
        model.summary()

        hyperparams_name = 'ResNet50'
        plot_model(model,"{}.png".format(hyperparams_name),show_shapes = True)

        path = os.path.join(self.data_path,'MODEL',hyperparams_name)

        if (os.path.exists(path) == False):
            os.makedirs(path)
            print("mkdir path:",path)

        # load nb_start_epoch model
        if self.nb_start_epoch > 0 :
            fname_param = os.path.join(path,'weights.{}.hdf5'.format(self.nb_start_epoch))
            print("load nb_start_epoch model: ",fname_param)
            model.load_weights(fname_param)

        # begin train model
        print ('begin fit the model')
        start_fit_time = time.time()

        fname_param = os.path.join(path,'weights.{epoch:d}.hdf5')
        model_checkpoint = ModelCheckpoint(fname_param, monitor='loss', verbose=1, save_best_only=True, mode='min',period=1)
        history = LossHistory()
        self.history=model.fit(X,Y,nb_epoch = self.nb_end_epoch,initial_epoch=self.nb_start_epoch, verbose=1, batch_size = self.batch_size, callbacks=[model_checkpoint,history],validation_data = [x_test,y_test])
        
        y_pred = model.predict(x_test)
        print(type(y_test),type(y_pred),y_test,y_pred)
        self.confmatrix = confusion_matrix(y_test.argmax(axis=1), y_pred.argmax(axis=1))
        elapsed = time.time() - start_fit_time
        print('train from {} epoch to {} epoch cost {}s'.format(self.nb_start_epoch,self.nb_end_epoch,elapsed))
        print("----------- print resnet50 train loss ----------")
        for i,iloss in enumerate(history.losses):
            print("epoch %d: %f" % ((i+1),iloss))

class TestModel(object):

	def __init__(self,model_path,batch_size,nb_start_epoch = 0):
		self.model_path = model_path
		self.batch_size = batch_size
		self.nb_start_epoch = nb_start_epoch

	def test_ResNet50(self,X,Y):

		model = resnet50()
		#model = incptv3()
		#model = onw_CNN()
		
		hyperparams_name = 'ResNet50'

		path = os.path.join(self.model_path,'MODEL',hyperparams_name)

		all_epoch = []
		all_jq = []
		# test all cont model
		for parent,dirnames,filenames in os.walk(path):
			print(filenames)
			for filename in filenames:
				#print('filename:',filename)
				epoch_index = int(filename.split(".")[1])
				
				if epoch_index > self.nb_start_epoch :
					
					print("epoch_index:",epoch_index)
					all_epoch.append(epoch_index)
					read_filename = os.path.join(parent,filename)
					print(read_filename)
					model.load_weights(read_filename)
					
					Y_predic_map = model.predict(X, batch_size = self.batch_size, verbose=1)
					print(Y_predic_map)
					print(Y)
					print("Y_predic_map.shape:",Y_predic_map.shape)
					
					jq = EvaluateSinglePrecision(Y,Y_predic_map)
					all_jq.append(jq)
		
		info = {}
		for i in range(len(all_epoch)):
			info[all_epoch[i]] =  str(all_jq[i])

		info_list = sorted(info.items(), key=lambda x:x[0], reverse=False) 

		print("epoch, Accuracy rate")
		for info_item in info_list:
			print (info_item)
		return info_list

# Plot Loss  
def plot_loss(model):
    plt.plot(model.history.history['loss'])
    plt.plot(model.history.history['val_loss'])
    plt.title('Model Loss--OwnCNN')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Training set', 'Test set'], loc='best')
    plt.show()
# Plot Accuracy 
def plot_accuracy(model):
    plt.plot(model.history.history['accuracy'])
    plt.plot(model.history.history['val_accuracy'])
    plt.title('Model Accuracy--ResNet50')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Training set', 'Validation set'], loc='best')
    plt.show()

# data augumentation
datagen = ImageDataGenerator(
    #rescale=1./255, 
    rotation_range=50,
    height_shift_range=[-0.05, 0, 0.05],
    width_shift_range=[-0.05, 0, 0.05],
    horizontal_flip=True,
    zca_whitening=True,
    fill_mode='reflect'
  )

for category in range(4):
  for home,dirs,files in os.walk('./train_dataset/'+str(category)+'/'):
      for filename in files:
          filenames = filename.split('.')
          if filenames[1] == 'jpeg':
              filename = './train_dataset/'+str(category)+'/'+filename
              img = load_img(filename)
              x = img_to_array(img) 
              x = x.reshape((1,) + x.shape) 
              i = 0
              for batch in datagen.flow(x,batch_size=1,save_to_dir='./train_dataset/'+str(category),save_prefix=filenames[0],save_format='jpeg'):
                i +=1
                if i > 3 :
                   break
'''
for home,dirs,files in os.walk('./train_dataset/3/'):
    for filename in files:
        filenames = filename.split('.')
        if filenames[1] == 'jpeg':
            filename = './train_dataset/3/'+filename
            img = load_img(filename)
            x = img_to_array(img) 
            x = x.reshape((1,) + x.shape) 
            i = 0
            for batch in datagen.flow(x,batch_size=1,save_to_dir='./train_dataset/3',save_prefix=filenames[0],save_format='jpeg'):
              i +=1
              if i > 3 :
                  break
'''

def read_img(filename):
    # load image
    img = load_img(filename) 
    # image to array
    x = img_to_array(img) 
    x = x.astype('float32')
    x /= 255
    return x

def create_dataset(dirname):
    x_train = []
    y_train = []
    y_train_temp = {}

    with open('train.txt','r') as f:
        content = f.read().splitlines()
    for i in content:
        key = i.split(',')[1].split('/')[1]
        if i.split(',')[2] == 'normal':
            value = 0
        elif i.split(',')[2] == 'viral':
            value = 1
        elif i.split(',')[2] == 'bacterial':
            value = 2
        elif i.split(',')[2] == 'covid':
            value = 3
        else:
            value = 4
        y_train_temp[key] = value 
    #print(y_train_temp.keys()) 

    for home,dirs,files in os.walk(dirname):
        for filename in files:
            filenames = filename.split('.')
            if filenames[1] == 'jpeg':
                tmp = filenames[0].split('_')[0]+'.jpeg'
                y = y_train_temp[tmp]
                filename = dirname+'/'+filename
                x = read_img(filename)
                y_train.append(y)
                x_train.append(x)
            #print(filename)
            
    x_train = np.array(x_train)
    y_train = np.array(y_train)
    #y_train = to_categorical(y_train)

    return x_train,y_train

x_train = []
y_train = []
x_test = []
y_test = []
for i in range(4):
  print('--------------',i)
  x,y = create_dataset('./train_dataset/'+str(i))
  print(x.shape,y.shape)
  '''
  divide = x.shape[0]//10 *7
  #print(int(divide))
  x_train_tmp = x[0:divide]
  y_train_tmp = y[0:divide]
  x_test_tmp = x[divide:len(x)]
  y_test_tmp = y[divide:len(y)]
  x_train = x_train + list(x_train_tmp)
  x_test = x_test + list(x_test_tmp)
  y_train = y_train + list(y_train_tmp)
  y_test = y_test + list(y_test_tmp)
  '''
  x_train = x_train + list(x)
  y_train = y_train + list(y)

for i in range(4):
  print('--------------',i)
  x,y = create_dataset('./test_dataset/'+str(i))
  print(x.shape,y.shape)
  x_test = x_test + list(x)
  y_test = y_test + list(y)

x_train = np.array(x_train)
y_train = np.array(y_train)
index = [i for i in range(len(x_train))] 
random.shuffle(index)
x_train = x_train[index]
y_train = y_train[index]

x_test = np.array(x_test)
y_test = np.array(y_test)
index = [i for i in range(len(x_test))] 
random.shuffle(index)
x_test = x_test[index]
y_test = y_test[index]

y_train = to_categorical(y_train)
y_test = to_categorical(y_test)
print('x_train.shape',x_train.shape)
print('y_train.shape',y_train.shape)

print('x_test.shape',x_test.shape)
print('y_test.shape',y_test.shape)

nb_start_epoch = 0
nb_end_epoch = 40
lr = 0.00001
batch_size = 32

train_root_path = "./model"
# strat train model #
train_model_path = os.path.join(train_root_path,'CNN')

if (os.path.exists(train_model_path) == False):
  os.makedirs(train_model_path)
  print("mkdir train_model_path:",train_model_path)

print("<"*5, "train on train data",">"*5)
train = TrainModel(train_model_path,lr,batch_size,nb_end_epoch = nb_end_epoch, nb_start_epoch=nb_start_epoch)
train.train_ResNet50(x_train,y_train,x_test,y_test)

cm_df = pd.DataFrame(train.confmatrix,
                     index = ['normal','viral','bacterial','covid'], 
                     columns = ['normal','viral','bacterial','covid'])

sns.heatmap(cm_df, annot=True,cmap="Blues")
plt.ylabel('True label')
plt.xlabel('Predicted label')
plt.show()

fig = plt.figure(figsize=(12,4))

fig.add_subplot(1,2,1)
plot_accuracy(train)

fig.add_subplot(1,2,2)
plot_loss(train)

plt.show()

#!rm -rf train_dataset
#!rm -rf test_dataset
#!rm -rf model

def load_read_test_img(filename):
    path = './test_dataset/'
    if (os.path.exists(path) == False):
      os.makedirs(path)
      print("mkdir path:",path)
    img = Image.open(filename)
    img = img.resize((256,256),Image.LANCZOS)
    filename_list = filename.split('/')
    filename = './test_dataset/'+filename_list[len(filename_list) - 1]
    img.save(filename)
    #print(filename)
    img = load_img(filename) # this is a PIL image # 
    # image to array
    x = img_to_array(img) 
    #print(x.shape)
    x = x.astype('float32')
    x /= 255
    return x
ID = []
x_test = []
path = "drive/My Drive/4771-sp20-covid/test/test"
for home,dirs,files in os.walk(path):
    for filename in files:
        filenames = filename.split('.')
        if filenames[1] == 'jpeg':
            ID.append(int(filename.split('-')[1].split('.')[0]))
            #ID[filename.split('-')[1].split('.')[0]] = 0
            filename = path+'/'+filename
            x = load_read_test_img(filename)
            x_test.append(x)

x_test = np.array(x_test)

r = {}
print(x_test.shape) 
model = resnet50()
model.load_weights('./model/CNN/MODEL/ResNet50/weights.4.hdf5')
Y_predic_map = model.predict(x_test, batch_size = 32, verbose=1)
print("Y_predic_map.shape:",Y_predic_map.shape)
for i in range(len(Y_predic_map)):
  l = list(Y_predic_map[i])
  max_index = l.index(max(l))# max ind 
  #print(i)
  if max_index == 0:
    r[ID[i]] = 'normal'
    #print(ID[i],'normal')
  elif max_index == 1:
    r[ID[i]] = 'viral'
    #print(ID[i],'viral')
  elif max_index == 2:
    r[ID[i]] = 'bacterial'
    #print(ID[i],'bacterial')
  elif max_index == 3:
    r[ID[i]] = 'covid'
    #print(ID[i],'covid')
print(r)
#df = pd.DataFrame.from_dict(r, orient="index")
for k in sorted(r):
    print(k,r[k])

