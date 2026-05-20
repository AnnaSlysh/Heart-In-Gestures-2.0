#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrain the keypoint classifier with:
  - Horizontal-mirror augmentation  -> makes the model work for BOTH hands
  - Class-weight balancing           -> compensates for Y (308) vs R (2429)

Run from the project root:
    python model/keypoint_classifier/retrain_with_mirror.py
"""

import csv
import numpy as np
import tensorflow as tf
from collections import Counter

KEYPOINT_CSV = 'model/keypoint.csv'
LABEL_CSV    = 'model/keypoint_classifier/keypoint_classifier_label.csv'
MODEL_KERAS  = 'model/keypoint_classifier/keypoint_classifier.keras'
MODEL_TFLITE = 'model/keypoint_classifier/keypoint_classifier.tflite'

NUM_FEATURES = 42   # 21 landmarks x 2 (x, y)


# ── Data ──────────────────────────────────────────────────────────────────────

def load_data():
    X, y = [], []
    with open(KEYPOINT_CSV, encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if not row:
                continue
            y.append(int(row[0]))
            X.append([float(v) for v in row[1:]])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def mirror_x(X):
    """Negate x-coordinates (even indices 0, 2, 4, ...) -- turns left hand into right hand."""
    m = X.copy()
    m[:, 0::2] = -m[:, 0::2]
    return m


# ── Model ─────────────────────────────────────────────────────────────────────

def build_model(num_classes):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(NUM_FEATURES,)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(num_classes, activation='softmax'),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with open(LABEL_CSV, encoding='utf-8-sig') as f:
        labels = [row[0] for row in csv.reader(f)]
    num_classes = len(labels)
    print("Classes ({}): {}".format(num_classes, labels))
    print()

    print("Loading training data ...")
    X, y = load_data()
    print("  Original samples : {}".format(len(X)))

    X_mirror = mirror_x(X)
    X_all = np.vstack([X, X_mirror])
    y_all = np.concatenate([y, y])
    print("  After mirroring  : {}".format(len(X_all)))
    print()

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(X_all))
    X_all, y_all = X_all[idx], y_all[idx]

    split = int(0.85 * len(X_all))
    X_train, X_val = X_all[:split], X_all[split:]
    y_train, y_val = y_all[:split], y_all[split:]
    print("Train : {}  |  Val : {}".format(len(X_train), len(X_val)))
    print()

    # Class weights to compensate for imbalance (Y=308 vs R=2429)
    counts = Counter(y_train.tolist())
    max_count = max(counts.values())
    class_weight = {c: max_count / counts[c] for c in counts}
    print("Class weights (most imbalanced):")
    for c in sorted(class_weight, key=lambda c: -class_weight[c])[:5]:
        print("  {:4s}: {:.2f}x".format(labels[c], class_weight[c]))
    print()

    model = build_model(num_classes)
    model.summary()
    print()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=20,
            restore_best_weights=True, verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=8, verbose=1,
        ),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=300,
        batch_size=64,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    model.save(MODEL_KERAS)
    print()
    print("Saved Keras model  -> {}".format(MODEL_KERAS))

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(MODEL_TFLITE, 'wb') as f_out:
        f_out.write(tflite_model)
    print("Saved TFLite model -> {}".format(MODEL_TFLITE))
    print()
    print("Done! Restart Streamlit to use the updated model.")


if __name__ == '__main__':
    main()
