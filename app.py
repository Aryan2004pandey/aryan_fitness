import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import threading
import time

# ----------------- Voice Engine ----------------- #
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)
voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[1].id)  # female if available

def speak(text):
    threading.Thread(
        target=lambda: engine.say(text) or engine.runAndWait(),
        daemon=True
    ).start()

# ----------------- Mediapipe Setup ----------------- #
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return angle if angle <= 180 else 360 - angle

def give_feedback(condition, good_msg, bad_msg):
    if condition:
        if good_msg: speak(good_msg)
        return good_msg, "#4CAF50"  # Green
    else:
        if bad_msg: speak(bad_msg)
        return bad_msg, "#FF5252"  # Red

# ----------------- Exercise Feedback ----------------- #
def squat_feedback(angle, back_angle):
    if angle < 70: return give_feedback(False, "", "Go deeper")
    elif angle > 120: return give_feedback(False, "", "Too low, rise up")
    elif back_angle < 160: return give_feedback(False, "", "Keep your back upright")
    else: return give_feedback(True, "Good squat!", "")

def pushup_feedback(elbow_angle, body_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms extended", "")
    elif elbow_angle < 90: return give_feedback(False, "", "Go lower in push-up")
    elif body_angle < 160: return give_feedback(False, "", "Keep body straight")
    else: return give_feedback(True, "Good push-up form!", "")

def bicep_feedback(elbow_angle):
    if elbow_angle > 160: return give_feedback(True, "Arm extended", "")
    elif elbow_angle < 40: return give_feedback(True, "Full curl!", "")
    else: return give_feedback(True, "Controlled curl", "")

def tricep_feedback(elbow_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms straightened fully", "")
    elif elbow_angle < 60: return give_feedback(False, "", "Bend your elbow more")
    else: return give_feedback(True, "Good tricep motion", "")

def shoulderpress_feedback(elbow_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms straight up", "")
    elif elbow_angle < 80: return give_feedback(False, "", "Push higher")
    else: return give_feedback(True, "Controlled press", "")

def jumpingjack_feedback(arm_angle, leg_angle):
    if arm_angle < 60 or leg_angle < 40: return give_feedback(False, "", "Jump wider")
    else: return give_feedback(True, "Good jumping jack", "")

def plank_feedback(body_angle):
    if body_angle < 160: return give_feedback(False, "", "Keep your body straight")
    else: return give_feedback(True, "Good plank hold", "")

def sidebend_feedback(body_angle):
    if body_angle < 150: return give_feedback(False, "", "Bend more to the side")
    else: return give_feedback(True, "Good side bend", "")

def mountainclimber_feedback(knee_angle):
    if knee_angle < 60: return give_feedback(True, "Drive knee in", "")
    else: return give_feedback(True, "Controlled motion", "")

# ----------------- Streamlit UI ----------------- #
st.set_page_config(page_title="AI Fitness Instructor", layout="wide")

# 🎨 Custom CSS
st.markdown("""
    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #f0f0f0;
        }
        .big-title {
            font-size: 42px;
            font-weight: 700;
            text-align: center;
            background: -webkit-linear-gradient(45deg, #42a5f5, #66bb6a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .feedback-box {
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            padding: 15px;
            border-radius: 12px;
            background: #1c1c1c;
        }
        .metric-box {
            text-align: center;
            background: #1976d2;
            padding: 15px;
            border-radius: 12px;
            color: white;
            font-size: 20px;
        }
        .sidebar .sidebar-content {
            background: #1e272e;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<p class='big-title'>🏋 AI Fitness Instructor</p>", unsafe_allow_html=True)
st.markdown("#### Real-time posture correction with *voice feedback & live rep counting*")

# Sidebar
st.sidebar.header("⚙ Controls")
exercise = st.sidebar.selectbox("Choose Exercise:",
    ["Squat", "Push-up", "Bicep Curl", "Triceps",
     "Shoulder Press", "Jumping Jack", "Plank",
     "Side Bend", "Mountain Climber"]
)

if "is_running" not in st.session_state:
    st.session_state.is_running = False
    st.session_state.counter = 0
    st.session_state.stage = None

if st.sidebar.button("▶ Start Camera"):
    st.session_state.is_running = True
    st.session_state.counter = 0
    st.session_state.stage = None

if st.sidebar.button("⏹ Stop Camera"):
    st.session_state.is_running = False

col1, col2 = st.columns([2, 1])
with col2:
    rep_placeholder = st.empty()
    feedback_placeholder = st.empty()
with col1:
    frame_placeholder = st.empty()

# ----------------- Camera Loop ----------------- #
if st.session_state.is_running:
    cap = cv2.VideoCapture(0)
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    while st.session_state.is_running:
        ret, frame = cap.read()
        if not ret:
            st.warning("⚠ Camera not detected.")
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        feedback_msg, color = "", "#ffffff"
        try:
            landmarks = results.pose_landmarks.landmark
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            # ---- Exercise Logic ---- #
            if exercise == "Squat":
                squat_angle = calculate_angle(hip, knee, ankle)
                back_angle = calculate_angle(shoulder, hip, knee)
                feedback_msg, color = squat_feedback(squat_angle, back_angle)
                if squat_angle > 140: st.session_state.stage = "up"
                if squat_angle < 90 and st.session_state.stage == "up":
                    st.session_state.stage, st.session_state.counter = "down", st.session_state.counter + 1

            elif exercise == "Push-up":
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                body_angle = calculate_angle(shoulder, hip, ankle)
                feedback_msg, color = pushup_feedback(elbow_angle, body_angle)
                if elbow_angle > 160: st.session_state.stage = "up"
                if elbow_angle < 90 and st.session_state.stage == "up":
                    st.session_state.stage, st.session_state.counter = "down", st.session_state.counter + 1

            elif exercise == "Bicep Curl":
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                feedback_msg, color = bicep_feedback(elbow_angle)
                if elbow_angle > 150: st.session_state.stage = "down"
                if elbow_angle < 40 and st.session_state.stage == "down":
                    st.session_state.stage, st.session_state.counter = "up", st.session_state.counter + 1

            elif exercise == "Triceps":
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                feedback_msg, color = tricep_feedback(elbow_angle)
                if elbow_angle < 60: st.session_state.stage = "down"
                if elbow_angle > 160 and st.session_state.stage == "down":
                    st.session_state.stage, st.session_state.counter = "up", st.session_state.counter + 1

            elif exercise == "Shoulder Press":
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                feedback_msg, color = shoulderpress_feedback(elbow_angle)
                if elbow_angle < 80: st.session_state.stage = "down"
                if elbow_angle > 160 and st.session_state.stage == "down":
                    st.session_state.stage, st.session_state.counter = "up", st.session_state.counter + 1

            elif exercise == "Jumping Jack":
                arm_angle = calculate_angle(shoulder, elbow, wrist)
                leg_angle = calculate_angle(hip, knee, ankle)
                feedback_msg, color = jumpingjack_feedback(arm_angle, leg_angle)
                if leg_angle > 100: st.session_state.stage = "open"
                if leg_angle < 60 and st.session_state.stage == "open":
                    st.session_state.stage, st.session_state.counter = "close", st.session_state.counter + 1

            elif exercise == "Plank":
                body_angle = calculate_angle(shoulder, hip, ankle)
                feedback_msg, color = plank_feedback(body_angle)

            elif exercise == "Side Bend":
                body_angle = calculate_angle(shoulder, hip, knee)
                feedback_msg, color = sidebend_feedback(body_angle)
                if body_angle < 150: st.session_state.stage = "bend"
                if body_angle > 170 and st.session_state.stage == "bend":
                    st.session_state.stage, st.session_state.counter = "up", st.session_state.counter + 1

            elif exercise == "Mountain Climber":
                knee_angle = calculate_angle(hip, knee, ankle)
                feedback_msg, color = mountainclimber_feedback(knee_angle)
                if knee_angle < 60: st.session_state.stage = "in"
                if knee_angle > 120 and st.session_state.stage == "in":
                    st.session_state.stage, st.session_state.counter = "out", st.session_state.counter + 1

            # --- Display Info ---
            rep_placeholder.markdown(
                f"<div class='metric-box'>🏆 Reps Completed: <b>{st.session_state.counter}</b></div>",
                unsafe_allow_html=True
            )
            feedback_placeholder.markdown(
                f"<div class='feedback-box' style='color:{color};'>{feedback_msg}</div>",
                unsafe_allow_html=True
            )

        except Exception:
            feedback_placeholder.warning("⚠ Stay in frame.")

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        frame_placeholder.image(image, channels="RGB")
        time.sleep(0.03)  # smooth 30 FPS

    cap.release()