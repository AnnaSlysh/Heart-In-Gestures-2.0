#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LSTM trainer for dynamic Ukrainian sign gestures.

Run from the GameModel1 root directory after collecting data:
    python model/dynamic_classifier/train.py
"""

import numpy as np
import os
import sys

DATA_DIR        = 'training_data/dynamic'
MODEL_OUT       = 'model/dynamic_classifier/dynamic_classifier.keras'
SEQUENCE_LENGTH = 15
NUM_FEATURES    = 42
EPOCHS          = 60
BATCH_SIZE      = 16
LABELS = ['Ґ', 'Д', 'Є', 'З', 'Ї', 'Й', 'К', 'Ц', 'Щ', 'Ь']


def load_data():
    X, y = [], []
    for class_idx in range(len(LABELS)):
        class_dir = os.path.join(DATA_DIR, str(class_idx))
        if not os.path.isdir(class_dir):
            continue
        files = [f for f in sorted(os.listdir(class_dir)) if f.endswith('.npy')]
        for fname in files:
            seq = np.load(os.path.join(class_dir, fname))
            if seq.shape == (SEQUENCE_LENGTH, NUM_FEATURES):
                X.append(seq)
                y.append(class_idx)
        print(f"  {LABELS[class_idx]}: {len(files)} samples")
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def build_model(num_classes):
    import tensorflow as tf
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(SEQUENCE_LENGTH, NUM_FEATURES)),
        tf.keras.layers.LSTM(64, return_sequences=True),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(num_classes, activation='softmax'),
    ])
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


def main():
    print("=== Dynamic Gesture LSTM Trainer ===\n")
    print("Loading data from", DATA_DIR)
    X, y = load_data()
    print(f"\nTotal: {len(X)} samples, {len(LABELS)} classes\n")

    if len(X) == 0:
        print("No data found! Run: python tools/collect_dynamic_data.py first.")
        sys.exit(1)

    classes_present = np.unique(y)
    if len(classes_present) < len(LABELS):
        missing = [LABELS[i] for i in range(len(LABELS)) if i not in classes_present]
        print(f"Warning: missing data for letters: {', '.join(missing)}")

    rng = np.random.default_rng(42)
    idx = rng.permutation(len(X))
    split = int(0.8 * len(X))
    X_train, X_val = X[idx[:split]], X[idx[split:]]
    y_train, y_val = y[idx[:split]], y[idx[split:]]
    print(f"Train: {len(X_train)}  |  Val: {len(X_val)}\n")

    import tensorflow as tf
    model = build_model(len(LABELS))
    model.summary()
    print()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=12, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, verbose=1
        ),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
    )

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    model.save(MODEL_OUT)
    print(f"\nModel saved → {MODEL_OUT}")
    print("You can now launch the game with full dynamic gesture support!")


if __name__ == '__main__':
    main()
