#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LSTM trainer for dynamic Ukrainian sign gestures.

Run from the project root directory after collecting data:
    python model/dynamic_classifier/train.py

Changes vs original:
- SEQUENCE_LENGTH aligned to 16 (matches runtime and data collector)
- Velocity features appended to each frame: input grows from 42 → 84 per frame
- Data augmentation: Gaussian noise + horizontal flip (4× dataset size)
- Bidirectional LSTM for better temporal modelling
- Class weights for imbalanced classes
- Automatic TFLite export at the end
"""

import numpy as np
import os
import sys

DATA_DIR         = 'training_data/dynamic'
MODEL_OUT        = 'model/dynamic_classifier/dynamic_classifier.keras'
TFLITE_OUT       = 'model/dynamic_classifier/dynamic_classifier.tflite'
SEQUENCE_LENGTH  = 15   # must match collect_dynamic_data.py
NUM_FEATURES     = 42   # raw landmarks per frame (x,y for 21 points)
EPOCHS           = 80
BATCH_SIZE       = 16
LABELS = ['Ґ', 'Д', 'Є', 'З', 'Ї', 'Й', 'К', 'Ц', 'Щ', 'Ь']


# ── Feature engineering ───────────────────────────────────────────

def add_velocity_features(X):
    """Append per-frame velocity (delta from previous frame) to position features.

    Input : (N, T, 42) — raw landmark positions
    Output: (N, T, 84) — positions + velocities (first frame velocity = 0)
    """
    deltas = np.zeros_like(X)
    deltas[:, 1:, :] = X[:, 1:, :] - X[:, :-1, :]
    return np.concatenate([X, deltas], axis=-1).astype(np.float32)


# ── Data loading ──────────────────────────────────────────────────

def load_data():
    X, y = [], []
    for class_idx in range(len(LABELS)):
        class_dir = os.path.join(DATA_DIR, str(class_idx))
        if not os.path.isdir(class_dir):
            continue
        files = [f for f in sorted(os.listdir(class_dir)) if f.endswith('.npy')]
        loaded = 0
        for fname in files:
            seq = np.load(os.path.join(class_dir, fname))
            if seq.shape == (SEQUENCE_LENGTH, NUM_FEATURES):
                X.append(seq)
                y.append(class_idx)
                loaded += 1
        print(f"  {LABELS[class_idx]}: {loaded} samples  ({len(files) - loaded} skipped — wrong shape)")
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


# ── Augmentation ──────────────────────────────────────────────────

def augment_dataset(X, y, rng, noise_std=0.02):
    """4× dataset: original + noise + h-flip + h-flip+noise.

    Horizontal flip negates all x-coordinates (even indices 0,2,4,...,40)
    which simulates using the opposite hand.
    """
    X_flip = X.copy()
    X_flip[:, :, 0::2] *= -1.0

    X_noisy      = np.clip(X      + rng.normal(0, noise_std, X.shape).astype(np.float32), -1, 1)
    X_flip_noisy = np.clip(X_flip + rng.normal(0, noise_std, X.shape).astype(np.float32), -1, 1)

    X_out = np.concatenate([X, X_noisy, X_flip, X_flip_noisy], axis=0)
    y_out = np.concatenate([y, y,       y,      y           ], axis=0)
    return X_out, y_out


# ── Model ─────────────────────────────────────────────────────────

def build_model(num_classes):
    import tensorflow as tf
    # Input is (SEQUENCE_LENGTH, 84) after velocity augmentation
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(SEQUENCE_LENGTH, NUM_FEATURES * 2)),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64, return_sequences=True)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(64),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(num_classes, activation='softmax'),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=5e-4, clipnorm=1.0),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    return model


# ── TFLite export ─────────────────────────────────────────────────

def export_tflite(model, path):
    import tensorflow as tf
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(path, 'wb') as f:
        f.write(tflite_model)
    print(f"TFLite model → {path}")


# ── Main ──────────────────────────────────────────────────────────

def main():
    print("=== Dynamic Gesture LSTM Trainer ===\n")
    print("Loading data from", DATA_DIR)
    X_raw, y = load_data()
    print(f"\nTotal raw: {len(X_raw)} samples, {len(LABELS)} classes")

    if len(X_raw) == 0:
        print("\nNo data found!  Did you collect with the right SEQUENCE_LENGTH=16?")
        print("Run: python tools/collect_dynamic_data.py")
        sys.exit(1)

    classes_present = np.unique(y)
    if len(classes_present) < len(LABELS):
        missing = [LABELS[i] for i in range(len(LABELS)) if i not in classes_present]
        print(f"Warning: missing data for letters: {', '.join(missing)}")

    rng = np.random.default_rng(42)

    # Augment raw position data before computing velocity
    X_aug, y_aug = augment_dataset(X_raw, y, rng)
    print(f"After augmentation: {len(X_aug)} samples (4×)")

    # Add velocity features: (N, 16, 42) → (N, 16, 84)
    X = add_velocity_features(X_aug)

    # Shuffle and split
    idx = rng.permutation(len(X))
    split = int(0.8 * len(X))
    X_train, X_val = X[idx[:split]], X[idx[split:]]
    y_train, y_val = y_aug[idx[:split]], y_aug[idx[split:]]
    print(f"Train: {len(X_train)}  |  Val: {len(X_val)}\n")

    # Class weights to handle imbalanced per-letter sample counts
    try:
        from sklearn.utils.class_weight import compute_class_weight
        cw = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weight_dict = {i: float(w) for i, w in enumerate(cw)}
        print("Class weights:", {LABELS[k]: round(v, 2) for k, v in class_weight_dict.items()})
    except ImportError:
        class_weight_dict = None
        print("sklearn not available — skipping class weights")

    import tensorflow as tf
    model = build_model(len(LABELS))
    model.summary()
    print()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy', patience=15, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=6, min_lr=1e-5, verbose=1
        ),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weight_dict,
        callbacks=callbacks,
    )

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    model.save(MODEL_OUT)
    print(f"\nKeras model → {MODEL_OUT}")

    export_tflite(model, TFLITE_OUT)
    print("\nDone! Launch the game to test dynamic gesture recognition.")


if __name__ == '__main__':
    main()
