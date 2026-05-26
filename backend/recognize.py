import cv2
import os
import pickle
import numpy as np
import face_recognition
<<<<<<< HEAD
=======
from paths import BASE_DIR,ATTENDANCE_DIR, ENCODINGS_DIR, IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR,FRONTEND_DIR
>>>>>>> ea91db6 (Face recogntion and document module integrated)

# =========================
#   LOAD ENCODINGS (.pkl)
# =========================
<<<<<<< HEAD
encoding_path = r"D:\CoreSight\backend\Dataset\Encodings"
=======
encoding_path = r"D:Projects\CoreSight\backend\Dataset\Encodings"
>>>>>>> ea91db6 (Face recogntion and document module integrated)
known_encodings = []
known_rolls = []

print("[INFO] Loading encodings from .pkl files...")

for file_name in os.listdir(encoding_path):
    if file_name.endswith(".pkl"):
        roll_no = os.path.splitext(file_name)[0]  # remove .pkl extension
        file_path = os.path.join(encoding_path, file_name)

        with open(file_path, "rb") as f:
            encoding = pickle.load(f)

        # Each file contains either a single encoding or a list/array of encodings
        if isinstance(encoding, list) or isinstance(encoding, np.ndarray):
            encoding = np.array(encoding)
            if encoding.ndim == 2:  # multiple encodings in one file
                encoding = np.mean(encoding, axis=0)
        else:
            continue  # skip invalid files

        known_encodings.append(encoding)
        known_rolls.append(roll_no)

print(f"[INFO] Loaded encodings for {len(known_encodings)} students.\n")

# =========================
#   REAL-TIME RECOGNITION
# =========================
video_capture = cv2.VideoCapture(0)
print("[INFO] Starting real-time recognition... Press 'q' to quit.\n")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Resize for faster processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect faces and get encodings
    face_locations = face_recognition.face_locations(rgb_small, model='cnn')
    face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

    for enc, loc in zip(face_encodings, face_locations):
        distances = face_recognition.face_distance(known_encodings, enc)
        best_idx = np.argmin(distances)
        roll_no = "Unknown"

        if distances[best_idx] < 0.45:
            roll_no = known_rolls[best_idx]

        # Scale coordinates back to full frame
        top, right, bottom, left = [v * 4 for v in loc]
        color = (0, 255, 0) if roll_no != "Unknown" else (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, roll_no, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Show the result
    cv2.imshow("Real-Time Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
