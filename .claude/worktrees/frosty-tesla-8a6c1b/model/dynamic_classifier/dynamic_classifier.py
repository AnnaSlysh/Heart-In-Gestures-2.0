#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os

MODEL_PATH = 'model/dynamic_classifier/dynamic_classifier.keras'


class DynamicGestureClassifier:
    def __init__(self):
        import tensorflow as tf
        self.model = tf.keras.models.load_model(MODEL_PATH)

    def __call__(self, sequence):
        """sequence: list of 15 lists of 42 floats, or (15, 42) ndarray."""
        x = np.array(sequence, dtype=np.float32).reshape(1, 15, 42)
        pred = self.model.predict(x, verbose=0)
        return int(np.argmax(pred[0]))


def model_exists():
    return os.path.exists(MODEL_PATH)
