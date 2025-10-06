import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from gtts import gTTS  # Pyttsx3 ki jagah cloud-friendly gTTS use ho raha hai
import io
import base64
import time  # Time module ko import kiya gaya hai (pichli error fix)

# ----------------- gTTS (Cloud-Friendly Voice Engine) ----------------- #
# Ye function audio file generate karke Streamlit ko play karne ke liye deta hai
def speak(text):
    # Sirf tabhi audio generate karein jab text ho
    if not text:
        return
    
    try:
        # gTTS object banao
        tts = gTTS(text, lang='en')
        
        # Audio data ko memory mein store karo
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Base64 encoding for Streamlit audio player
        audio_b64 = base64.b64encode(fp.read()).decode()
        
        # Streamlit ke liye HTML audio tag
        audio_html = f"""
        <audio controls autoplay style="display:none">
          <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
        </audio>
        """
        # Streamlit markdown mein render karo
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        # Agar gTTS fail ho (internet ya service issue), toh error ko ignore karein
        print(f"gTTS Error: {e}")

# ----------------- Mediapipe Setup ----------------- #
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return angle if angle <= 180 else 360 - angle

# --- Feedback Function Updated for gTTS ---
def give_feedback(condition, good_msg, bad_msg):
    # Streamlit session state mein last spoken message store karte hain
    last_spoken = st.session_state.get('last_spoken', time.time() - 5)
    
    # Har 3 seconds mein ek hi message dobara nahi bolenge (spamming rokne ke liye)
    if time.time() - last_spoken > 3:
        if condition and good_msg:
            st.session_state.last_spoken = time.time()
            speak(good_msg)
            return good_msg, "#4CAF50"  # Green
        elif not condition and bad_msg:
            st.session_state.last_spoken = time.time()
            speak(bad_msg)
            return bad_msg, "#FF5252"  # Red
    
    # Agar bolne ki condition satisfy nahi hui, toh sirf text return karo
    if condition:
        return good_msg, "#4CAF50"
    else:
        return bad_msg, "#FF5252"


# ----------------- Exercise Feedback (No Logic Change) ----------------- #
def squat_feedback(angle, back_angle):
    if angle < 70: return give_feedback(False, "", "Go deeper")
    elif angle > 120: return give_feedback(False, "", "Too low, rise up")
    elif back_angle < 160: return give_feedback(False, "", "Keep your back upright")
    else: return give_feedback(True, "Good squat!", "Good squat!") # Good message bhi repeat hota hai jab condition true ho

def pushup_feedback(elbow_angle, body_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms extended", "")
    elif elbow_angle < 90: return give_feedback(False, "", "Go lower in push-up")
    elif body_angle < 160: return give_feedback(False, "", "Keep body straight")
    else: return give_feedback(True, "Good push-up form!", "Good push-up form!")

def bicep_feedback(elbow_angle):
    if elbow_angle > 150: return give_feedback(True, "Arm extended", "Arm extended")
    elif elbow_angle < 40: return give_feedback(True, "Full curl!", "Full curl!")
    else: return give_feedback(True, "Controlled curl", "Controlled curl")

def tricep_feedback(elbow_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms straightened fully", "Arms straightened fully")
    elif elbow_angle < 60: return give_feedback(False, "", "Bend your elbow more")
    else: return give_feedback(True, "Good tricep motion", "Good tricep motion")

def shoulderpress_feedback(elbow_angle):
    if elbow_angle > 160: return give_feedback(True, "Arms straight up", "Arms straight up")
    elif elbow_angle < 80: return give_feedback(False, "", "Push higher")
    else: return give_feedback(True, "Controlled press", "Controlled press")

def jumpingjack_feedback(arm_angle, leg_angle):
    if arm_angle < 60 or leg_angle < 40: return give_feedback(False, "", "Jump wider")
    else: return give_feedback(True, "Good jumping jack", "Good jumping jack")

def plank_feedback(body_angle):
    if body_angle < 160: return give_feedback(False, "", "Keep your body straight")
    else: return give_feedback(True, "Good plank hold", "Good plank hold")

def sidebend_feedback(body_angle):
    if body_angle < 150: return give_feedback(False, "", "Bend more to the side")
    else: return give_feedback(True, "Good side bend", "Good side bend")

def mountainclimber_feedback(knee_angle):
    if knee_angle < 60: return give_feedback(True, "Drive knee in", "Drive knee in")
    else: return give_feedback(True, "Controlled motion", "Controlled motion")


# ----------------- Streamlit UI ----------------- #
st.set_page_config(page_title="AI Fitness Instructor", layout="wide")

# 🎨 Custom CSS
st.markdown("""
    <style>
        /* ... CSS same rakha gaya hai ... */
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
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<p class='big-title'>🏋 AI Fitness Instructor</p>", unsafe_allow_html=True)
st.markdown("#### Real-time posture correction with voice feedback & live rep counting")

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
    st.session_state.last_spoken = time.time() # gTTS timer ko initialize kiya gaya

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
    # 0 ki jagah 'video_source' variable use karna behtar hai, but for simplicity 0 rakha
    cap = cv2.VideoCapture(0)
    # MediaPipe pose object ko loop ke bahar define karna behtar hai performance ke liye
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    while st.session_state.is_running:
        ret, frame = cap.read()
        if not ret:
            st.warning("⚠ Camera not detected or frame could not be read.")
            # Camera stop button ko press karne ki zarurat pad sakti hai
            st.session_state.is_running = False 
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Image ko non-writable banane se MediaPipe ki performance badhti hai
        image.flags.writeable = False 
        results = pose.process(image)
        image.flags.writeable = True

        feedback_msg, color = "", "#ffffff"
        try:
            landmarks = results.pose_landmarks.landmark
            # ... Landmark calculation same ...
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

            # ---- Exercise Logic (same as original) ---- #
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
        # time.sleep(0.03) ko Streamlit mein hata diya hai

    cap.release()
