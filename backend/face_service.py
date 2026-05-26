# =========================================================
#          CoreSight - Face Recognition Service
# =========================================================

import os
import io
import pickle
import numpy as np
import face_recognition
from PIL import Image
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

# =========================================================
# Router
# =========================================================
router = APIRouter(tags=["Face Recognition"])

# =========================================================
# Paths (same as main.py)
# =========================================================
from paths import BASE_DIR,ATTENDANCE_DIR, ENCODINGS_DIR, IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR,FRONTEND_DIR

# =========================================================
# Shared In-Memory Encodings
# =========================================================
known_encodings: list = []
known_rolls: list = []

# =========================================================
# Load Encodings (on startup)
# =========================================================
def load_encodings():
    known_encodings.clear()
    known_rolls.clear()

    if not os.path.exists(ENCODINGS_DIR):
        return

    for file in os.listdir(ENCODINGS_DIR):
        if not file.endswith(".pkl"):
            continue

        try:
            with open(os.path.join(ENCODINGS_DIR, file), "rb") as f:
                data = pickle.load(f)

            if isinstance(data, dict):
                known_encodings.append(data["encoding"])
                known_rolls.append(data["roll_no"])
            else:
                known_encodings.append(np.array(data))
                known_rolls.append(os.path.splitext(file)[0])

        except Exception as e:
            print(f"[ERROR] Failed loading {file}: {e}")

    print(f"[FACE] Loaded encodings: {len(known_encodings)}")

# =========================================================
# Reload Encodings (called after register / upload)
# =========================================================
def reload_encodings():
    load_encodings()

# Load once at import
load_encodings()

# =========================================================
# Face Recognition Endpoint
# =========================================================
@router.post("/recognize-faces")
async def recognize_faces(frame: UploadFile = File(...)):
    image_bytes = await frame.read()
    image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

    face_encs = face_recognition.face_encodings(image)
    recognized = []
    profiles = []

    if not face_encs:
        return {"recognized_faces": [], "profiles": []}

    for enc in face_encs:
        distances = face_recognition.face_distance(known_encodings, enc)

        if len(distances) == 0:
            recognized.append("Unknown")
            continue

        best = np.argmin(distances)

        if distances[best] < 0.45:
            roll_no = known_rolls[best]
            recognized.append(roll_no)
            profiles.append({"roll_no": roll_no})
        else:
            recognized.append("Unknown")

    return {
        "recognized_faces": recognized,
        "profiles": profiles
    }
