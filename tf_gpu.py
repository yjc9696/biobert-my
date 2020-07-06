import os

import tensorflow as tf
os.environ["CUDA_VISIBLE_DEVICES"] = '2'   #指定第一块GPU可用
tf.test.is_gpu_available()