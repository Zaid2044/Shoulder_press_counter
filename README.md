# AI Shoulder Press Counter with Audio Feedback

This Python application utilizes your webcam, MediaPipe Pose estimation, and Pygame to count shoulder press repetitions in real-time. It provides visual feedback on the current stage of the press (up/down), the total rep count, and optional audio cues for completed movements.


## Features

-   **Real-time Pose Estimation:** Employs Google's MediaPipe Pose to detect 33 body landmarks.
-   **Shoulder Press Rep Counting:** Tracks elbow angles and wrist positions relative to shoulders to determine the "up" (arms extended overhead) and "down" (hands at shoulder level) stages of a shoulder press.
-   **Visual Feedback:** Displays the current repetition count, exercise stage ("UP", "DOWN", "START"), and contextual feedback on the video feed.
-   **Audio Feedback (Optional):** Plays distinct sounds for completing the "up" and "down" phases of the exercise using Pygame. Includes a cooldown mechanism to prevent sound spam.
-   **Webcam Input:** Uses your default webcam for live video processing.
-   **Cross-Platform:** Built with Python, OpenCV, MediaPipe, and Pygame.

## Technologies Used

-   **Python 3.x**
-   **OpenCV (`opencv-python`)**: For video capture, image manipulation, and display.
-   **MediaPipe (`mediapipe`)**: For high-fidelity body pose tracking.
-   **NumPy (`numpy`)**: For numerical operations, especially angle calculations.
-   **Pygame (`pygame`)**: For playing audio feedback.
-   **Time (`time`)**: For managing audio feedback cooldowns.

## Prerequisites

-   Python 3 installed on your system.
-   A webcam.
-   (Optional but Recommended) Two short audio files (e.g., `.mp3` format) for the "up" and "down" movement cues. Name them `Up.mp3` and `Down.mp3` and place them in the same directory as the script, or update the paths in the code.

## Installation

1.  **Clone the repository (or download the `shoulder_press_counter.py` file):**
    ```bash
    # If you create a git repo:
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install numpy opencv-python mediapipe pygame
    ```

4.  **Prepare Audio Files (Optional):**
    -   Obtain or create two short sound files (e.g., `.mp3`).
    -   Name them `Up.mp3` and `Down.mp3`.
    -   Place them in the same directory as the `shoulder_press_counter.py` script.
    -   If you use different filenames or locations, update the `SOUND_UP_PATH` and `SOUND_DOWN_PATH` variables in the script.
    -   If audio files are not found or Pygame has issues, audio feedback will be automatically disabled.

## Usage

1.  Navigate to the directory where `shoulder_press_counter.py` (and your audio files, if using) are located.
2.  Ensure your virtual environment is activated (if you created one).
3.  Run the script from your terminal:
    ```bash
    python shoulder_press_counter.py
    ```
4.  A window will open showing your webcam feed with pose landmarks, the counter, and feedback.
5.  Perform shoulder presses facing the camera. Ensure your shoulders, elbows, and wrists are clearly visible throughout the movement.
    -   **Down Position:** Hands at or slightly above shoulder level, elbows bent.
    -   **Up Position:** Arms extended fully overhead.
6.  Listen for audio cues if enabled and configured.
7.  Press the **'q'** key to quit the application.

## How It Works

1.  **Video Capture & Preprocessing:** OpenCV captures frames, which are then flipped horizontally and converted to RGB for MediaPipe.
2.  **Pose Estimation:** MediaPipe Pose detects body landmarks.
3.  **Landmark Extraction & Angle Calculation:** Coordinates for shoulders, elbows, and wrists are extracted. The `calculate_angle` function computes the elbow angles.
4.  **Shoulder Press Logic:**
    -   **"Up" Stage:** Determined by arms being relatively straight (large elbow angle) AND wrists being significantly above the shoulders (Y-coordinate of wrist < Y-coordinate of shoulder).
    -   **"Down" Stage:** Determined by arms being bent (smaller elbow angle) AND wrists being at or near shoulder level.
    -   A repetition is counted when transitioning from the "down" stage to the "up" stage.
5.  **Audio Feedback:**
    -   Pygame is used to play pre-defined sound files.
    -   A cooldown timer (`AUDIO_COOLDOWN_DURATION`) prevents sounds from playing too rapidly.
    -   Flags (`played_sound_for_up`, `played_sound_for_down`) ensure each distinct movement completion sound plays only once per cycle.
6.  **Visualization:**
    -   Pose landmarks and connections are drawn on the video frame.
    -   A status box displays rep count, current stage, and textual feedback.

## Customization and Tuning

-   **Thresholds:** The accuracy of the counter heavily depends on the angle and position thresholds:
    -   `ANGLE_ARM_EXTENDED`
    -   `ANGLE_ARM_BENT`
    -   `WRIST_Y_ABOVE_SHOULDER_FACTOR`
    You will likely need to **tune these values** based on your camera setup, individual biomechanics, and desired strictness. Print the live angle and Y-coordinate values to the console during testing to help find optimal thresholds.
-   **Audio Files:** Use any `.wav` (or other Pygame-supported) audio files you prefer.
-   **Feedback Messages:** Customize the `feedback` string for more specific instructions or encouragement.
-   **Single Arm Tracking:** Modify the logic if you want to track each arm independently.

## Potential Improvements

-   **Advanced Form Correction:** Implement checks for common mistakes (e.g., excessive back arch, incomplete range of motion).
-   **User Profiles:** Allow users to save their preferred thresholds.
-   **Exercise Selection:** Expand to include other exercises by creating different logic modules.
-   **GUI:** Develop a more polished graphical user interface.
