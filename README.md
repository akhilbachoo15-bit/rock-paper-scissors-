# Gesture-Controlled Rock Paper Scissors

A real-time Rock Paper Scissors game you play with your hand in front of a webcam. Hand tracking is done with MediaPipe, and the interface is drawn with OpenCV.

**Tech:** Python, OpenCV, MediaPipe

## Features

- Real-time hand tracking with a skeleton overlay
- Gesture recognition for Rock, Paper and Scissors
- Countdown and hold-to-confirm lock-in, so accidental gestures don't count
- First-to-3 match with a live score HUD
- Clickable on-screen buttons (Start, Next Round, Rematch, Exit) plus keyboard shortcuts

## Requirements

- Python 3.9+
- A webcam
- The MediaPipe hand landmarker model file (`hand_landmarker.task`)

## Setup

1. Install the dependencies:

   ```bash
   pip install opencv-python mediapipe
   ```

2. Download the hand landmarker model and place it in the same folder as the script:

   ```
   https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
   ```

3. Run the game:

   ```bash
   python rps_game_simple.py
   ```

If the wrong camera opens, change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`.

## How to play

1. Click **START** (or press `S`).
2. Wait for the countdown to finish.
3. When "SHOW IT!" appears, make a gesture and hold it steady until the bar fills:

   | Gesture | Hand shape |
   |---|---|
   | Rock | Closed fist |
   | Paper | Open palm, all fingers up |
   | Scissors | Index and middle fingers up |

4. The computer picks at random and the round result is shown.
5. First to 3 wins takes the match. Click **REMATCH** (or press `R`) to play again.

## Controls

| Action | Mouse | Keyboard |
|---|---|---|
| Start / next round | START / NEXT ROUND button | `S` or `Space` |
| Rematch | REMATCH button | `R` |
| Exit | EXIT button | `ESC` or `Q` |

## How it works

1. **Capture:** OpenCV reads frames from the webcam and mirrors them.
2. **Tracking:** MediaPipe's Hand Landmarker returns 21 landmarks for the hand in each frame.
3. **Recognition:** a finger counts as "up" when its tip is above its base on screen (the thumb is checked sideways, using the left/right hand label). All fingers down is Rock, all up is Paper, and only index and middle up is Scissors.
4. **Game flow:** a small state machine runs idle, countdown, show gesture, result and match over.
5. **Efficiency:** the hand model only runs while a round is live.

## Settings

These are at the top of the script:

| Setting | Default | Description |
|---|---|---|
| `COUNTDOWN` | `5` | Seconds before you show your gesture |
| `HOLD_TIME` | `0.6` | Seconds a gesture must be held to lock in |
| `WINS_NEEDED` | `3` | Round wins needed to take the match |

## Limitations

- Tracks one hand at a time
- Works best with an upright hand facing the camera in good lighting
- Gesture detection is rule-based rather than a trained classifier

## Ideas for improvement

- Replace the rules with a trained gesture classifier
- Add sound effects and animations
- Add a best-of-N option and persistent stats
