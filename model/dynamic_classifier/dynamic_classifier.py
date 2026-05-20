#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os

MODEL_PATH      = 'model/dynamic_classifier/dynamic_classifier.tflite'
SEQUENCE_LENGTH = 16    # frames per gesture sequence
LANDMARK_DIM    = 42    # 21 landmarks × 2 (x, y)
SCORE_TH        = 0.65  # raised from 0.5 — rejects uncertain predictions


class DynamicGestureClassifier:
    def __init__(self):
        import tensorflow as tf
        self.interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        # Auto-detect whether model expects flat (1, 672) or sequential (1, 16, 42)
        self._lstm = (len(self.input_details[0]['shape']) == 3)

    def __call__(self, sequence):
        """sequence: list of SEQUENCE_LENGTH lists of 42 floats.
        Returns predicted class index, or -1 if confidence is below threshold.
        """
        if self._lstm:
            inp = np.array([sequence], dtype=np.float32)  # (1, 16, 42)
        else:
            flat = np.array(
                [v for frame in sequence for v in frame], dtype=np.float32
            )
            inp = np.array([flat])  # (1, 672)
        self.interpreter.set_tensor(self.input_details[0]['index'], inp)
        self.interpreter.invoke()
        scores = np.squeeze(
            self.interpreter.get_tensor(self.output_details[0]['index'])
        )
        idx = int(np.argmax(scores))
        return idx if scores[idx] >= SCORE_TH else -1


def model_exists():
    return os.path.exists(MODEL_PATH)
