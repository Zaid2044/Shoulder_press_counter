# shoulder_press_counter.py

import numpy as np
import cv2          # OpenCV for computer vision tasks
import mediapipe as mp # Google's MediaPipe for pose estimation
import time         # For cooldown timers for audio feedback
import pygame       # For playing audio feedback

# --- Pygame Mixer Initialization for Audio ---
try:
    pygame.mixer.init()
    SOUND_UP_PATH = "Up.mp3" # Replace with your actual path or filename
    SOUND_DOWN_PATH = "Down.mp3" # Replace with your actual path or filename
    sound_up = pygame.mixer.Sound(SOUND_UP_PATH)
    sound_down = pygame.mixer.Sound(SOUND_DOWN_PATH)
    audio_enabled = True
    print("Audio enabled. Ensure sound_up.wav and sound_down.wav are present.")
except pygame.error as e:
    print(f"Pygame mixer error: {e}. Audio feedback will be disabled.")
    audio_enabled = False
except FileNotFoundError:
    print("Audio files (sound_up.wav or sound_down.wav) not found. Audio feedback will be disabled.")
    audio_enabled = False


# --- Helper Function to Calculate Angle ---
def calculate_angle(a, b, c):
    """
    Calculates the angle between three 2D points (forming a joint).
    Args:
        a: Numpy array or list representing the first point [x, y].
        b: Numpy array or list representing the middle point (vertex) [x, y].
        c: Numpy array or list representing the third point [x, y].
    Returns:
        angle: The calculated angle in degrees.
    """
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

# --- Main Shoulder Press Tracking Function ---
def shoulder_press_tracker():
    """
    Main function to run the shoulder press tracker using webcam feed and MediaPipe Pose.
    """
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video device.")
        return

    # Rep counter variables
    counter = 0
    stage = None  # "down" (hands at shoulder level, ready to press), "up" (arms extended overhead)
    feedback = "START"

    # Audio feedback cooldown variables
    AUDIO_COOLDOWN_DURATION = 1.5  # seconds
    last_audio_play_time = 0
    # Flags to ensure sound plays only once per stage completion
    played_sound_for_up = False
    played_sound_for_down = False


    # Drawing specifications
    landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2) # Green for landmarks
    connection_drawing_spec = mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2) # Blue for connections

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose_estimator:
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("Error: Can't receive frame (stream end?). Exiting ...")
                    break

                frame_flipped = cv2.flip(frame, 1)
                image_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = pose_estimator.process(image_rgb)
                
                # Get frame dimensions for converting normalized coordinates
                frame_height, frame_width, _ = frame_flipped.shape

                try:
                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark
                        
                        # --- Get coordinates for LEFT arm ---
                        shoulder_l_coords = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                        elbow_l_coords = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
                        wrist_l_coords = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]

                        shoulder_l = [shoulder_l_coords.x, shoulder_l_coords.y]
                        elbow_l = [elbow_l_coords.x, elbow_l_coords.y]
                        wrist_l = [wrist_l_coords.x, wrist_l_coords.y]
                        
                        # --- Get coordinates for RIGHT arm ---
                        shoulder_r_coords = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                        elbow_r_coords = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
                        wrist_r_coords = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]

                        shoulder_r = [shoulder_r_coords.x, shoulder_r_coords.y]
                        elbow_r = [elbow_r_coords.x, elbow_r_coords.y]
                        wrist_r = [wrist_r_coords.x, wrist_r_coords.y]
                        
                        # Calculate elbow angles
                        angle_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
                        angle_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
                        
                        # --- Shoulder Press Logic ---
                        # For shoulder press, we need:
                        # 1. Elbow angle (extended for "up", bent for "down")
                        # 2. Wrist position relative to shoulder (wrists above shoulders for "up")
                        # MediaPipe Y coordinates are 0 at top, 1 at bottom.
                        
                        # Thresholds (these may need tuning)
                        ANGLE_ARM_EXTENDED = 155  # Angle when arm is considered extended up
                        ANGLE_ARM_BENT = 100      # Angle when arm is considered bent at shoulder level
                        WRIST_Y_ABOVE_SHOULDER_FACTOR = 0.05 # Wrist must be at least 5% of frame height above shoulder for "up"

                        # "UP" Stage: Arms extended overhead
                        # Both wrists must be above their respective shoulders AND arms relatively straight
                        is_up_l = (angle_l > ANGLE_ARM_EXTENDED and wrist_l_coords.y < shoulder_l_coords.y - WRIST_Y_ABOVE_SHOULDER_FACTOR)
                        is_up_r = (angle_r > ANGLE_ARM_EXTENDED and wrist_r_coords.y < shoulder_r_coords.y - WRIST_Y_ABOVE_SHOULDER_FACTOR)

                        # "DOWN" Stage: Hands at/near shoulder height, arms bent
                        # Both wrists near or below shoulder height AND arms bent
                        is_down_l = (angle_l < ANGLE_ARM_BENT and wrist_l_coords.y > shoulder_l_coords.y - (WRIST_Y_ABOVE_SHOULDER_FACTOR * 2)) # allow slightly above shoulder
                        is_down_r = (angle_r < ANGLE_ARM_BENT and wrist_r_coords.y > shoulder_r_coords.y - (WRIST_Y_ABOVE_SHOULDER_FACTOR * 2))


                        current_time = time.time()

                        if is_up_l and is_up_r:
                            if stage == "down": # Transition from down to up
                                counter += 1
                                feedback = f"UP! Rep: {counter}"
                                print(f"Rep: {counter}")
                                if audio_enabled and not played_sound_for_up and (current_time - last_audio_play_time > AUDIO_COOLDOWN_DURATION):
                                    sound_up.play()
                                    last_audio_play_time = current_time
                                    played_sound_for_up = True
                                    played_sound_for_down = False # Reset for next down movement
                            stage = "up"
                        elif is_down_l and is_down_r:
                            if stage == "up": # Transition from up to down
                                feedback = "DOWN - Ready"
                                if audio_enabled and not played_sound_for_down and (current_time - last_audio_play_time > AUDIO_COOLDOWN_DURATION):
                                    sound_down.play()
                                    last_audio_play_time = current_time
                                    played_sound_for_down = True
                                    played_sound_for_up = False # Reset for next up movement
                            elif stage is None: # Initial state
                                feedback = "Ready (Arms Down)"

                            stage = "down"
                        
                        # Provide continuous feedback based on dominant arm if not perfectly synced (optional)
                        if not (is_up_l and is_up_r) and not (is_down_l and is_down_r):
                            if stage == "down":
                                if (angle_l > ANGLE_ARM_BENT + 20 or wrist_l_coords.y < shoulder_l_coords.y - WRIST_Y_ABOVE_SHOULDER_FACTOR or
                                    angle_r > ANGLE_ARM_BENT + 20 or wrist_r_coords.y < shoulder_r_coords.y - WRIST_Y_ABOVE_SHOULDER_FACTOR):
                                    feedback = "Press Up!"
                            elif stage == "up":
                                if (angle_l < ANGLE_ARM_EXTENDED - 20 or wrist_l_coords.y > shoulder_l_coords.y or
                                    angle_r < ANGLE_ARM_EXTENDED - 20 or wrist_r_coords.y > shoulder_r_coords.y):
                                    feedback = "Extend Fully!"
                    else:
                        feedback = "No pose detected"
                        stage = None # Reset stage if pose is lost

                except Exception as e:
                    feedback = f"Error: {str(e)[:30]}" # Show brief error on screen
                    pass 
                
                # --- Drawing UI Elements ---
                cv2.rectangle(frame_flipped, (0,0), (int(frame_width * 0.8), 70), (50,50,50), -1) # Wider box
                
                cv2.putText(frame_flipped, 'REPS', (15,25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA)
                cv2.putText(frame_flipped, str(counter), 
                            (20,60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,0), 2, cv2.LINE_AA)
                
                cv2.putText(frame_flipped, 'STAGE', (int(frame_width * 0.2), 25), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA)
                cv2.putText(frame_flipped, stage if stage else "START", 
                            (int(frame_width * 0.2) + 5, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,0), 2, cv2.LINE_AA)

                cv2.putText(frame_flipped, f"FDBK: {feedback}", (int(frame_width * 0.45), 45), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2, cv2.LINE_AA)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(frame_flipped, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                            landmark_drawing_spec, connection_drawing_spec)               
                
                cv2.imshow('Shoulder Press Tracker', frame_flipped)

                if cv2.waitKey(10) & 0xFF == ord('q'):
                    print("Exiting program...")
                    break
        finally:
            print("Releasing resources...")
            if cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
            if audio_enabled:
                pygame.mixer.quit() # Important to quit pygame mixer
            print("Resources released.")

if __name__ == '__main__':
    shoulder_press_tracker()
