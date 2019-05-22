# -*- coding: utf-8 -*-
"""My Food101.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xzXpwBqSJi2OLRmySE9Q1g6L2IGjdUgk

# Multiclass Classification using Keras and TensorFlow 2.0 on Food-101 Dataset
#[alt text](https://www.vision.ee.ethz.ch/datasets_extra/food-101/static/img/food-101.jpg)

### Overview
* **Download and extract Food 101 dataset**
* **Understand dataset structure and files** 
* **Visualize random image from each of the 101 classes**
* **Split the image data into train and test using train.txt and test.txt**
* **Create a subset of data with few classes(3) - train_mini and test_mini for experimenting**
* **Fine tune Inception Pretrained model using Food 101 dataset**
* **Visualize accuracy and loss plots**
* **Predicting classes for new images from internet**
* **Scale up and fine tune Inceptionv3 model with 11 classes of data**
* **Summary of the things I tried**
* **Further improvements**
* **Feedback**

### Download and extract Food 101 Dataset
"""



# Check if GPU is enabled
import tensorflow as tf
print(tf.__version__)
print(tf.test.gpu_device_name())

# Helper function to download data and extract
import os
from pathlib import Path


import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np
from collections import defaultdict
import collections

foods_sorted = sorted(os.listdir("food101/images"))

# Helper method to split dataset into train and test folders
from shutil import copy
def prepare_data(filepath, src,dest):
    classes_images = defaultdict(list)
    with open(filepath, 'r') as txt:
        paths = [read.strip() for read in txt.readlines()]
        for p in paths:
            food = p.split('/')
            classes_images[food[0]].append(food[1] + '.jpg')

    for food in classes_images.keys():
        print("\nCopying images into ",food)
        if not os.path.exists(os.path.join(dest,food)):
            os.makedirs(os.path.join(dest,food))
        if not len(os.listdir(os.path.join(dest,food))) == 250:    
            for i in classes_images[food]:
                if not Path(os.path.join(dest,food,i)).is_file():
                    copy(os.path.join(src,food,i), os.path.join(dest,food,i))
        return Path(dest)
    print("Copying Done#")


# Prepare train dataset by copying images from food-101/images to food-101/train using the file train.txt
print("Creating train data...")
prepare_data('food101/meta/train.txt', 'food101/images', 'food101/train')
exit(0)

# Prepare test data by copying images from food-101/images to food-101/test using the file test.txt
print("Creating test data...")
prepare_data('food101/meta/test.txt', 'food101/images', 'food101/test')

# Check how many files are in the train folder
print("Total number of samples in train folder")
#find 'food101/train' -type d -or -type f -printf '.' | wc -c

# Check how many files are in the test folder
print("Total number of samples in test folder")
#find 'food101/test' -type d -or -type f -printf '.' | wc -c

"""### Create a subset of data with few classes(3) - train_mini and test_mini for experimenting

* We now have train and test data ready  
* But to experiment and try different architectures, working on the whole data with 101 classes takes a lot of time and computation  
* To proceed with further experiments, I am creating train_min and test_mini, limiting the dataset to 3 classes  
* Since the original problem is multiclass classification which makes key aspects of architectural decisions different from that of binary classification, choosing 3 classes is a good start instead of 2
"""

# List of all 101 types of foods(sorted alphabetically)
#foods_sorted

# Helper method to create train_mini and test_mini data samples
from shutil import copytree, rmtree


dest_train = 'food101/train'
dest_test = 'food101/test'

"""
* Keras and other Deep Learning libraries provide pretrained models  
* These are deep neural networks with efficient architectures(like VGG,Inception,ResNet) that are already trained on datasets like ImageNet  
* Using these pretrained models, we can use the already learned weights and add few layers on top to finetune the model to our new data  
* This helps in faster convergance and saves time and computation when compared to models trained from scratch

* We currently have a subset of dataset with 3 classes - samosa, pizza and omelette  
* Use the below code to finetune Inceptionv3 pretrained model
"""
# Helper function to select n random food classes
import random
def pick_n_random_classes(n):
  food_list = []
  random_food_indices = random.sample(range(len(foods_sorted)),n) # We are picking n random food classes
  for i in random_food_indices:
    food_list.append(foods_sorted[i])
  food_list.sort()
  print("These are the randomly picked food classes we will be training the model on...\n", food_list)
  return food_list

# Lets try with more classes than just 3. Also, this time lets randomly pick the food classes
n = 1
food_list = pick_n_random_classes(n)

import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras import regularizers
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D, AveragePooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from tensorflow.keras.optimizers import SGD

def training():
    K.clear_session()

    img_width, img_height = 299, 299
    train_data_dir = dest_train
    validation_data_dir = dest_test
    nb_train_samples = 750#75750
    nb_validation_samples = 250#25250
    batch_size = 16

    train_datagen = ImageDataGenerator(
        rescale=1. / 255,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True)

    test_datagen = ImageDataGenerator(rescale=1. / 255)

    train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size=(img_height, img_width),
        batch_size=batch_size,
        class_mode='categorical')

    validation_generator = test_datagen.flow_from_directory(
        validation_data_dir,
        target_size=(img_height, img_width),
        batch_size=batch_size,
        class_mode='categorical')


    inception = InceptionV3(weights='imagenet', include_top=False)
    x = inception.output
    x = GlobalAveragePooling2D()(x)
    x = Dense(128,activation='relu')(x)
    x = Dropout(0.2)(x)

    predictions = Dense(3,kernel_regularizer=regularizers.l2(0.005), activation='softmax')(x)

    model = Model(inputs=inception.input, outputs=predictions)
    model.compile(optimizer=SGD(lr=0.0001, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy'])
    checkpointer = ModelCheckpoint(filepath='food101/best_model_101class.hdf5', verbose=1, save_best_only=True)
    csv_logger = CSVLogger('food101/history.log')


    history = model.fit_generator(train_generator,
                        steps_per_epoch = nb_train_samples // batch_size,
                        validation_data=validation_generator,
                        validation_steps=nb_validation_samples // batch_size,
                        epochs=1,
                        verbose=1,
                        callbacks=[csv_logger, checkpointer])


    model.save('model_trained_101class.hdf5')
    return model

training()

import matplotlib.pyplot as plt

def plot_accuracy(history,title):
    plt.title(title)
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train_accuracy', 'validation_accuracy'], loc='best')
    plt.show()
def plot_loss(history,title):
    plt.title(title)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train_loss', 'validation_loss'], loc='best')
    plt.show()


# plot_accuracy(history,'FOOD101-Inceptionv3')
# plot_loss(history,'FOOD101-Inceptionv3')

"""* **The plots show that the accuracy of the model increased with epochs and the loss has decreased**
* **Validation accuracy has been on the higher side than training accuracy for many epochs**
* **This could be for several reasons:**
  * We used a pretrained model trained on ImageNet which contains data from a variety of classes
  * Using dropout can lead to a higher validation accuracy
* **The best model saved has a Top-1 validation accuracy of 93%**

### Predicting classes for new images from internet using the best trained model


# Loading the best saved model to make predictions
# %%time
import tensorflow.keras.backend as K
from tensorflow.keras.models import load_model

K.clear_session()
##ls '/content/gdrive/My Drive/Sistemi-ICSE2'
#model_best = load_model('/content/gdrive/My Drive/Sistemi-ICSE2/model_trained_3class.hdf5',compile = False)

* **Setting compile=False and clearing the session leads to faster loading of the saved model**
* **Withouth the above addiitons, model loading was taking more than a minute#**


from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt
import numpy as np
import os

def predict_class(model, images, show = True):
  for img in images:
    img = image.load_img(img, target_size=(299, 299))
    img = image.img_to_array(img)                    
    img = np.expand_dims(img, axis=0)         
    img /= 255.                                      

    pred = model.predict(img)
    index = np.argmax(pred)
    food_list.sort()
    pred_value = food_list[index]
    if show:
        plt.imshow(img[0])                           
        plt.axis('off')
        plt.title(pred_value)
        plt.show()
  return pred_value

# Downloading images from internet using the URLs
#wget -O samosa.jpg http://veggiefoodrecipes.com/wp-content/spell/2016/05/lentil-samosa-recipe-01.jpg
#wget -O pizza.jpg http://104.130.3.186/assets/itemimages/400/400/3/default_9b4106b8f65359684b3836096b4524c8_pizza%20dreamstimesmall_94940296.jpg
#wget -O omelette.jpg https://www.incredibleegg.org/wp-content/spell/basic-french-omelet-930x550.jpg

# If you have an image in your local computer and want to try it, uncomment the below code to upload the image files

# from google.colab import files
# image = files.upload()

# Make a list of downloaded images and test the trained model
images = []
images.append('samosa.jpg')
images.append('pizza.jpg')
images.append('omelette.jpg')
predict_class(model_best, images, True)

* **Yes### The model got them all right##**

### Fine tune Inceptionv3 model with 11 classes of data

* **We trained a model on 3 classes and tested it using new data**
* ** The model was able to predict the classes of all three test images correctly**
* **Will it be able to perform at the same level of accuracy for more classes?**
* **FOOD-101 dataset has 101 classes of data**
* ** Even with fine tuning using a pre-trained model, each epoch was taking more than an hour when all 101 classes of data is used(tried this on both Colab and on a Deep Learning VM instance with P100 GPU on GCP)**
* **But to check how the model performs when more classes are included, I'm using the same model to fine tune and train on 11 randomly chosen classes**


# Helper function to select n random food classes
import random
def pick_n_random_classes(n):
  food_list = []
  random_food_indices = random.sample(range(len(foods_sorted)),n) # We are picking n random food classes
  for i in random_food_indices:
    food_list.append(foods_sorted[i])
  food_list.sort()
  print("These are the randomly picked food classes we will be training the model on...\n", food_list)
  return food_list

# Lets try with more classes than just 3. Also, this time lets randomly pick the food classes
n = 101
food_list = pick_n_random_classes(n)

# Create the new data subset of n classes
print("Creating training data folder with new classes...")
dataset_mini(food_list, src_train, dest_train)

print("Total number of samples in train folder")
#find '/content/gdrive/My Drive/Sistemi-ICSE2/food-101/food-101/train' -type d -or -type f -printf '.' | wc -c

print("Creating test data folder with new classes")
dataset_mini(food_list, src_test, dest_test)

print("Total number of samples in test folder")
#find '/content/gdrive/My Drive/Sistemi-ICSE2/food-101/food-101/test' -type d -or -type f -printf '.' | wc -c

# Let's use a pretrained Inceptionv3 model on subset of data with 11 food classes

import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.keras import regularizers
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D, GlobalAveragePooling2D, AveragePooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, CSVLogger
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.regularizers import l2
from tensorflow import keras
import numpy as np

K.clear_session()

n_classes = n
img_width, img_height = 299, 299
train_data_dir = '/content/gdrive/My Drive/Sistemi-ICSE2/food-101/food-101/train'
validation_data_dir = '/content/gdrive/My Drive/Sistemi-ICSE2/food-101/food-101/test'
nb_train_samples = 75750 #75750
nb_validation_samples = 25250 #25250
batch_size = 16

train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

test_datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical')

validation_generator = test_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode='categorical')


inception = InceptionV3(weights='imagenet', include_top=False)
x = inception.output
x = GlobalAveragePooling2D()(x)
x = Dense(128,activation='relu')(x)
x = Dropout(0.2)(x)

predictions = Dense(n,kernel_regularizer=regularizers.l2(0.005), activation='softmax')(x)

model = Model(inputs=inception.input, outputs=predictions)
model.compile(optimizer=SGD(lr=0.0001, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy'])
checkpointer = ModelCheckpoint(filepath='/content/gdrive/My Drive/Sistemi-ICSE2/logs/best_model_101class.hdf5', verbose=1, save_best_only=True)
csv_logger = CSVLogger('history_101.log')

for i in range(10):
    if not os.listdir('/content/gdrive/My Drive/Sistemi-ICSE2/logs'):
        print('Empty dir')
        history = model.fit_generator(train_generator,
                        steps_per_epoch = nb_train_samples // batch_size,
                        validation_data=validation_generator,
                        validation_steps=nb_validation_samples // batch_size,
                        epochs=1,
                        verbose=1,
                        callbacks=[csv_logger, checkpointer])
        #ls '/content/gdrive/My Drive/Sistemi-ICSE2/logs'
    else:
        print('Not empty dir')
        #ls '/content/gdrive/My Drive/Sistemi-ICSE2/logs'
        model = load_model('/content/gdrive/My Drive/Sistemi-ICSE2/logs/best_model_101class.hdf5')
        history = model.fit_generator(train_generator,
                            steps_per_epoch = nb_train_samples // batch_size,
                            validation_data=validation_generator,
                            validation_steps=nb_validation_samples // batch_size,
                            epochs=1,
                            verbose=1,
                            callbacks=[csv_logger, checkpointer])





 CODICE AGGIUNTO DA ME PER SALVARE SU DRIVE IL MODELLO
from google.colab import drive
drive.mount('/content/gdrive')
model.save("/content/gdrive/My Drive/Sistemi-ICSE2/logs/model_trained_101class.hdf5")
print('salvato SALVATO')
 CODICE PER CARICARE IL MODELLO 
from keras.models import load_model
model = load_model(<path to your model file on local machine>)
"""

""" FINE CODICE AGGIUNTO DA ME 

plot_accuracy(history_11class,'FOOD101-Inceptionv3')
plot_loss(history_11class,'FOOD101-Inceptionv3')

 **The plots show that the accuracy of the model increased with epochs and the loss has decreased**
* **Validation accuracy has been on the higher side than training accuracy for many epochs**
* **This could be for several reasons:**
  * We used a pretrained model trained on ImageNet which contains data from a variety of classes
  * Using dropout can lead to a higher validation accuracy
* **I set number of epochs to just 10, as each epoch's taking around 6mins**
* **loss is still decreasing, so the model can have some more epochs**
* **Increase the number of epochs for better accuracy**
"""
"""
# Loading the best saved model to make predictions
# %%time
from tensorflow.keras.models import load_model
import tensorflow.keras.backend as K
K.clear_session()
#model_best = load_model('best_model_11class.hdf5',compile = False)
model_best = load_model("/content/gdrive/My Drive/Sistemi-ICSE/model_trained_101class.hdf5",compile = False)

# Downloading images from internet using the URLs
#wget -O frenchfries.jpg https://www.dirtyapronrecipes.com/wp-content/spell/2017/03/french-fries.jpg
#wget -O chocolatecake.jpg https://tastesbetterfromscratch.com/wp-content/spell/2010/06/Hersheys-Perfectly-Chocolate-Chocolate-Cake-13.jpg
#wget -O waffles.jpg https://upload.wikimedia.org/wikipedia/commons/5/5b/Waffles_with_Strawberries.jpg
#wget -O applepie.jpg https://www.theseasonedmom.com/wp-content/spell/2018/08/Moms-Easy-Apple-Pie-10-500x375.jpg
#unzip '/content/gdrive/My Drive/Sistemi-ICSE/risotto.zip'
# If you have an image in your local computer and want to try it, uncomment the below code to upload the image files


# from google.colab import files
# image = files.upload()

# Make a list of downloaded images and test the trained model
images = []
images.append('frenchfries.jpg')
images.append('chocolatecake.jpg')
images.append('applepie.jpg')
images.append('waffles.jpg')
images.append('risotto.jpg')
predict_class(model_best, images, True)

* **The model did well even when the number of classes are increased to 11**
* **Model training on all 101 classes takes some time**
* ** It was taking more than an hour for one epoch when the full dataset is used for fine tuning**

### Summary of the things I tried
* **This notebook is the refactored and organised version of all the experiments and training trials I made**
* **I used this very useful Keras blog - https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html for reference**
* **I spent considerable amount of time in fixing things even before getting to the model training phase**
* **For example, it took some time to get the image visualization plots aligned withouth any overlap**
* **It is easier to go through a notebook and understand code someone else has taken hours to finish**
* **I started with VGG16 pretrained model. It did give good validation accuracy after training for few epochs**
* **I then tried Inceptionv3. VGG was taking more time for each epoch and since inception was also giving good validation accuracy, I chose Inception over VGG**
* **I ran both VGG and Inception with two different image sizes - 150 X  50 and 299 X 299**
* **I had better results with larger image size and hence chose 299 X 299**
* **For data augmentation, I sticked to the transformations used in the above blog**
* **I didnt use TTA except rescaling test images**
* **To avoid Colab connection issues during training, I set number of epochs to 10**
* **As the loss is still decreasing after 10 epochs both with 3-class and 11-class subset of data, the model can be trained for some more epochs for better accuracy**

### Further Improvements
* **Try more augmentation on test images**
* **Fine tune the model on the entire dataset(for a few epochs atleast)**
* **Play with hyper parameters, their values and see how it impacts model performance**
* **There is currently no implementation to handle out of distribution / no class scenario. Can try below methods:**
    * Set a threshold for the class with highest score. When model gives prediction score below the threshold for its top prediction, the prediction can be classified as NO-CLASS / UNSEEN
    * Add a new class called **NO-CLASS**, provide data from different classes other than those in the original dataset. This way the model also learns how to classify totally unseen/unrelated data
    * I am yet to try these methods and not sure about the results
* ** Recently published paper - [Rethinking ImageNet Pretraining](https://arxiv.org/abs/1811.08883 ), claims that training from random initialization instead of using pretrained weights is not only robust but also gives comparable results**
* **Pre-trained models are surely helpful. They save a lot of time and computation. Yet, that shouldn't be the reason to not try to train a model from scratch**
* **Time taking yet productive experiment would be to try and train a model on this dataset from scratch**

### Feedback

* **Did you find any issues with the above code or have any suggestions or corrections?**
* **There must be many ways to improve the model, its architecture, hyperparameters..**
* **Please do let me know#**
* **[Avinash Kappa](https://theimgclist.github.io/)**
* **[Twitter](https://twitter.com/avinashso13)**
* **[Linkedin](https://www.linkedin.com/in/avinash-kappa)**
"""
