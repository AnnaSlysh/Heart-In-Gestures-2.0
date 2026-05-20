#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dynamic gesture data collection tool.

Run from the GameModel1 root directory:
    python tools/collect_dynamic_data.py

Controls:
    SPACE  - Start a 15-frame recording burst
    r      - Discard the last saved sample (undo)
    n      - Skip to the next letter without finishing
    q      - Quit and save progress
"""

import cv2 as cv
import mediapipe as mp
import numpy as np
import copy
import itertools
import os
import sys
import time

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ── Config ────────────────────────────────────────────────────────
DYNAMIC_LETTERS = ['Ґ', 'Д', 'Є', 'З', 'Ї', 'Й', 'К', 'Ц', 'Щ', 'Ь']
SAMPLES_PER_LETTER = 50
SEQUENCE_LENGTH    = 15
RECORD_INTERVAL    = 0.13   # seconds between captured frames (~7-8 fps)
DATA_DIR           = 'training_data/dynamic'


# ── Landmark helpers (same normalization as recognition.py) ───────
def calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    pts = []
    for lm in landmarks.landmark:
        pts.append([min(int(lm.x * w), w - 1),
                    min(int(lm.y * h), h - 1)])
    return pts


def pre_process_landmark(landmark_list):
    tmp = copy.deepcopy(landmark_list)
    bx, by = tmp[0]
    for p in tmp:
        p[0] -= bx
        p[1] -= by
    flat = list(itertools.chain.from_iterable(tmp))
    mx = max(map(abs, flat)) or 1
    return [v / mx for v in flat]


# ── PIL text overlay (supports Cyrillic on Windows) ───────────────
def _load_font(size):
    for path in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def put_text(frame, text, pos, size=36, color=(255, 255, 255), bold=False):
    rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil)
    font = _load_font(size)
    if bold:
        # crude bold: draw twice with 1px offset
        draw.text((pos[0] + 1, pos[1] + 1), text, font=font, fill=color)
    draw.text(pos, text, font=font, fill=color)
    return cv.cvtColor(np.array(pil), cv.COLOR_RGB2BGR)


def draw_ui(frame, letter, letter_idx, count, status, progress):
    """Overlay all UI text and indicators on the frame."""
    h, w = frame.shape[:2]

    # Semi-transparent top bar
    overlay = frame.copy()
    cv.rectangle(overlay, (0, 0), (w, 110), (0, 0, 0), -1)
    cv.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    # Letter being recorded (large, centered)
    frame = put_text(frame, letter, (w // 2 - 30, 8), size=72, bold=True,
                     color=(100, 255, 150))

    # Letter index
    frame = put_text(frame,
                     f"Letter {letter_idx + 1} / {len(DYNAMIC_LETTERS)}",
                     (12, 12), size=26, color=(200, 200, 200))

    # Sample count
    frame = put_text(frame,
                     f"Samples: {count} / {SAMPLES_PER_LETTER}",
                     (12, 46), size=26, color=(200, 200, 200))

    # Status line
    color_map = {
        'READY':      (180, 180, 180),
        'RECORDING':  (80,  200, 80),
        'SAVED':      (80,  180, 255),
        'NO HAND':    (80,   80, 255),
    }
    frame = put_text(frame, status,
                     (12, 78), size=24,
                     color=color_map.get(status, (255, 255, 255)))

    # Recording progress bar
    if progress > 0:
        bar_w = int((w - 24) * progress / SEQUENCE_LENGTH)
        cv.rectangle(frame, (12, h - 22), (12 + bar_w, h - 8),
                     (80, 200, 80), -1)
        cv.rectangle(frame, (12, h - 22), (w - 12, h - 8),
                     (100, 100, 100), 1)
        frame = put_text(frame,
                         f"{progress} / {SEQUENCE_LENGTH} frames",
                         (w // 2 - 60, h - 48), size=22,
                         color=(200, 200, 200))

    # Controls hint
    frame = put_text(frame,
                     "SPACE=record  r=undo  n=skip letter  q=quit",
                     (12, h - 72), size=20, color=(140, 140, 140))
    return frame


# ── Main ──────────────────────────────────────────────────────────
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for i in range(len(DYNAMIC_LETTERS)):
        os.makedirs(os.path.join(DATA_DIR, str(i)), exist_ok=True)

    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH,  960)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 540)

    mp_hands   = mp.solutions.hands
    hands_model = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )

    letter_idx = 0
    status     = 'READY'
    recording  = False
    seq_buffer = []
    last_cap_t = 0.0

    # Count already-collected samples per letter
    counts = []
    for i in range(len(DYNAMIC_LETTERS)):
        d = os.path.join(DATA_DIR, str(i))
        counts.append(len([f for f in os.listdir(d) if f.endswith('.npy')]))

    # Skip letters already complete
    while letter_idx < len(DYNAMIC_LETTERS) and \
          counts[letter_idx] >= SAMPLES_PER_LETTER:
        letter_idx += 1

    if letter_idx >= len(DYNAMIC_LETTERS):
        print("All samples collected! Run: python model/dynamic_classifier/train.py")
        return

    print("\n=== Dynamic Gesture Data Collection ===")
    print(f"Collecting {SAMPLES_PER_LETTER} samples per letter for: "
          + ", ".join(DYNAMIC_LETTERS))
    print("Run from the GameModel1 root directory.\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv.flip(frame, 1)

        image_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results   = hands_model.process(image_rgb)

        landmarks = None
        if results.multi_hand_landmarks:
            lm_raw    = results.multi_hand_landmarks[0]
            lm_list   = calc_landmark_list(frame, lm_raw)
            landmarks = pre_process_landmark(lm_list)
            # Draw hand skeleton
            mp.solutions.drawing_utils.draw_landmarks(
                frame, lm_raw, mp_hands.HAND_CONNECTIONS)

        now = time.time()

        if recording:
            if now - last_cap_t >= RECORD_INTERVAL:
                last_cap_t = now
                seq_buffer.append(landmarks if landmarks else [0.0] * 42)
                status = 'RECORDING'

            if len(seq_buffer) >= SEQUENCE_LENGTH:
                # Save the sequence
                seq_np  = np.array(seq_buffer, dtype=np.float32)
                save_to = os.path.join(DATA_DIR, str(letter_idx),
                                       f"{counts[letter_idx]:04d}.npy")
                np.save(save_to, seq_np)
                counts[letter_idx] += 1
                recording  = False
                seq_buffer = []
                status     = 'SAVED'
                print(f"  [{DYNAMIC_LETTERS[letter_idx]}] "
                      f"{counts[letter_idx]}/{SAMPLES_PER_LETTER} saved")

                if counts[letter_idx] >= SAMPLES_PER_LETTER:
                    print(f"Letter {DYNAMIC_LETTERS[letter_idx]} complete!")
                    letter_idx += 1
                    while letter_idx < len(DYNAMIC_LETTERS) and \
                          counts[letter_idx] >= SAMPLES_PER_LETTER:
                        letter_idx += 1
                    if letter_idx >= len(DYNAMIC_LETTERS):
                        print("\nAll samples collected!")
                        print("Run: python model/dynamic_classifier/train.py")
                        break
        else:
            if landmarks:
                status = 'READY'
            else:
                status = 'NO HAND'

        frame = draw_ui(
            frame,
            DYNAMIC_LETTERS[letter_idx],
            letter_idx,
            counts[letter_idx],
            status,
            len(seq_buffer),
        )

        cv.imshow('Dynamic Data Collection — press Q to quit', frame)

        key = cv.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and not recording:
            recording  = True
            seq_buffer = []
            last_cap_t = time.time()
            status     = 'RECORDING'
        elif key == ord('r') and not recording and counts[letter_idx] > 0:
            # Undo last saved sample
            counts[letter_idx] -= 1
            path = os.path.join(DATA_DIR, str(letter_idx),
                                f"{counts[letter_idx]:04d}.npy")
            if os.path.exists(path):
                os.remove(path)
            print(f"  [{DYNAMIC_LETTERS[letter_idx]}] Removed last sample "
                  f"({counts[letter_idx]} remaining)")
        elif key == ord('n') and not recording:
            print(f"  Skipping letter {DYNAMIC_LETTERS[letter_idx]}")
            letter_idx += 1
            if letter_idx >= len(DYNAMIC_LETTERS):
                print("All letters skipped / done.")
                break

    hands_model.close()
    cap.release()
    cv.destroyAllWindows()

    print("\nCollection summary:")
    for i, letter in enumerate(DYNAMIC_LETTERS):
        print(f"  {letter}: {counts[i]} / {SAMPLES_PER_LETTER} samples")


if __name__ == '__main__':
    main()
