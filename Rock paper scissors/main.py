import math
import random
import time

import cv2
from mediapipe import Image, ImageFormat
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------- Settings ----------------
MODEL_PATH = "hand_landmarker.task"
COUNTDOWN = 5        # seconds before you show your gesture
HOLD_TIME = 0.6      # seconds to hold a gesture to lock it in
WINS_NEEDED = 3

WHITE, GRAY, ACCENT = (255, 255, 255), (170, 170, 170), (255, 200, 0)
GREEN, RED, YELLOW = (0, 210, 0), (0, 0, 230), (0, 210, 210)
FONT = cv2.FONT_HERSHEY_SIMPLEX

CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
               (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15),
               (15, 16), (0, 17), (17, 18), (18, 19), (19, 20),
               (5, 9), (9, 13), (13, 17)]

# ---------------- Game state ----------------
# state: idle -> countdown -> show -> result -> (countdown ... | over)
g = dict(state="idle", user=0, cpu=0, user_pick="-", cpu_pick="-", result="",
         t0=0.0, hold=None, hold_t=0.0, ts=0, mouse=(-1, -1), click=False, quit=False)


def new_round():
    g.update(state="countdown", t0=time.time(), hold=None, result="", user_pick="-", cpu_pick="-")


def reset_match():
    g.update(state="idle", user=0, cpu=0, user_pick="-", cpu_pick="-", result="")


def finish_round(user_pick):
    cpu_pick = random.choice(["Rock", "Paper", "Scissors"])
    beats = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    if user_pick == cpu_pick:
        result = "Draw"
    elif beats[user_pick] == cpu_pick:
        result = "You Win!"
        g["user"] += 1
    else:
        result = "Computer Wins!"
        g["cpu"] += 1
    g.update(user_pick=user_pick, cpu_pick=cpu_pick, result=result, state="result")
    if WINS_NEEDED in (g["user"], g["cpu"]):
        g["state"] = "over"


# ---------------- Gesture detection ----------------
def get_gesture(lm, hand):
    thumb = lm[4].x > lm[2].x if hand == "Right" else lm[4].x < lm[2].x
    fingers = [lm[t].y < lm[b].y for t, b in ((8, 5), (12, 9), (16, 13), (20, 17))]
    up = [thumb] + fingers
    if not any(up):
        return "Rock"
    if all(up):
        return "Paper"
    if up == [False, True, True, False, False]:
        return "Scissors"
    return None


def detect(frame):
    """Run the hand model, draw the skeleton, return the gesture (or None)."""
    h, w = frame.shape[:2]
    g["ts"] = max(int(time.time() * 1000), g["ts"] + 1)  # timestamps must increase
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = landmarker.detect_for_video(Image(image_format=ImageFormat.SRGB, data=rgb), g["ts"])
    if not res.hand_landmarks:
        return None
    lm = res.hand_landmarks[0]
    pts = [(int(p.x * w), int(p.y * h)) for p in lm]
    for a, b in CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], (255, 180, 0), 2, cv2.LINE_AA)
    for p in pts:
        cv2.circle(frame, p, 5, (0, 255, 150), -1, cv2.LINE_AA)
    return get_gesture(lm, res.handedness[0][0].category_name)


# ---------------- Drawing ----------------
def text(frame, s, y, scale=0.8, color=WHITE, thick=2, x=None):
    """Draw text with a shadow, centered horizontally unless x is given."""
    size = cv2.getTextSize(s, FONT, scale, thick)[0]
    x = (frame.shape[1] - size[0]) // 2 if x is None else x
    cv2.putText(frame, s, (x + 2, y + 2), FONT, scale, (0, 0, 0), thick + 1, cv2.LINE_AA)
    cv2.putText(frame, s, (x, y), FONT, scale, color, thick, cv2.LINE_AA)


def panel(frame, x1, y1, x2, y2, alpha=0.6):
    roi = frame[y1:y2, x1:x2]
    cv2.addWeighted(roi * 0, alpha, roi, 1 - alpha, 0, roi)  # darken the region


def button(frame, rect, label, color):
    """Draw a button; returns True if it was clicked this frame."""
    x1, y1, x2, y2 = rect
    mx, my = g["mouse"]
    hover = x1 <= mx <= x2 and y1 <= my <= y2
    fill = tuple(min(255, c + 50) for c in color) if hover else color
    cv2.rectangle(frame, (x1, y1), (x2, y2), fill, -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), WHITE, 2 if hover else 1)
    size = cv2.getTextSize(label, FONT, 0.6, 2)[0]
    cv2.putText(frame, label, (x1 + (x2 - x1 - size[0]) // 2, y1 + (y2 - y1 + size[1]) // 2),
                FONT, 0.6, WHITE, 2, cv2.LINE_AA)
    if hover and g["click"]:
        g["click"] = False
        return True
    return False


def on_mouse(event, x, y, flags, param):
    g["mouse"] = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN:
        g["click"] = True


def draw_hud(frame):
    w = frame.shape[1]
    panel(frame, 0, 0, w, 90)
    text(frame, "YOU", 28, 0.5, GRAY, 1, x=16)
    text(frame, g["user_pick"], 65, 0.8, ACCENT, 2, x=16)
    text(frame, "CPU", 28, 0.5, GRAY, 1, x=w - 110)
    text(frame, g["cpu_pick"], 65, 0.8, ACCENT, 2, x=w - 110)
    text(frame, f"{g['user']} - {g['cpu']}", 55, 1.3, WHITE, 3)
    text(frame, f"First to {WINS_NEEDED}", 80, 0.45, GRAY, 1)


def draw_center(frame, now):
    h = frame.shape[0]
    cy = h // 2 + 20
    state = g["state"]

    if state == "idle":
        panel(frame, 120, cy - 80, frame.shape[1] - 120, cy + 70)
        text(frame, "ROCK PAPER SCISSORS", cy - 35, 0.9, ACCENT)
        text(frame, "Fist = Rock   Palm = Paper   2 fingers = Scissors", cy + 5, 0.5, WHITE, 1)
        text(frame, f"First to {WINS_NEEDED} wins the match", cy + 40, 0.55, GRAY, 1)

    elif state == "countdown":
        remaining = COUNTDOWN - (now - g["t0"])
        n = max(1, math.ceil(remaining))
        text(frame, "GET READY", cy - 70, 0.8)
        text(frame, str(n), cy + 40, 3.2 - 0.9 * (n - remaining), ACCENT, 5)

    elif state == "show":
        if g["hold"]:
            text(frame, g["hold"].upper(), cy, 1.3, GREEN, 3)
            progress = min(1, (now - g["hold_t"]) / HOLD_TIME)
            w = frame.shape[1]
            cv2.rectangle(frame, (w // 2 - 100, cy + 25), (w // 2 - 100 + int(200 * progress), cy + 40), GREEN, -1)
            cv2.rectangle(frame, (w // 2 - 100, cy + 25), (w // 2 + 100, cy + 40), WHITE, 1)
        else:
            text(frame, "SHOW IT!", cy, 1.5, ACCENT, 4)

    elif state == "result":
        color = {"You Win!": GREEN, "Computer Wins!": RED}.get(g["result"], YELLOW)
        text(frame, g["result"], cy, 1.4, color, 3)

    elif state == "over":
        panel(frame, 0, cy - 70, frame.shape[1], cy + 50, 0.75)
        won = g["user"] > g["cpu"]
        text(frame, "YOU WIN THE MATCH!" if won else "COMPUTER WINS THE MATCH!",
             cy, 1.0, GREEN if won else RED, 3)


# ---------------- Setup ----------------
landmarker = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
))

cap = cv2.VideoCapture(0)   # use 1 for an external webcam
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

WINDOW = "Rock Paper Scissors"
cv2.namedWindow(WINDOW)
cv2.setMouseCallback(WINDOW, on_mouse)

# ---------------- Main loop ----------------
while cap.isOpened() and not g["quit"]:
    ok, frame = cap.read()
    if not ok:
        time.sleep(0.01)
        continue

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    now = time.time()

    # Detect only while a round is live
    gesture = detect(frame) if g["state"] in ("countdown", "show") else None

    # Round logic
    if g["state"] == "countdown" and now - g["t0"] >= COUNTDOWN:
        g["state"] = "show"
    if g["state"] == "show":
        if gesture != g["hold"]:                      # gesture changed: restart hold timer
            g["hold"], g["hold_t"] = gesture, now
        elif gesture and now - g["hold_t"] >= HOLD_TIME:
            finish_round(gesture)

    # Drawing
    draw_hud(frame)
    draw_center(frame, now)

    # Buttons
    if g["state"] in ("idle", "result"):
        label = "START (S)" if g["state"] == "idle" else "NEXT ROUND (S)"
        if button(frame, (w // 2 - 100, h - 60, w // 2 + 100, h - 16), label, (70, 170, 70)):
            new_round()
    elif g["state"] == "over":
        if button(frame, (w // 2 - 100, h - 60, w // 2 + 100, h - 16), "REMATCH (R)", (70, 170, 70)):
            reset_match()
    if button(frame, (w - 120, h - 60, w - 12, h - 16), "EXIT (ESC)", (60, 60, 200)):
        g["quit"] = True

    cv2.imshow(WINDOW, frame)
    g["click"] = False

    # Keyboard
    key = cv2.waitKey(1) & 0xFF
    if key in (27, ord("q")):
        g["quit"] = True
    elif key in (ord("s"), 32) and g["state"] in ("idle", "result"):
        new_round()
    elif key == ord("r") and g["state"] == "over":
        reset_match()

    # Window closed with the title-bar X
    if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
landmarker.close()