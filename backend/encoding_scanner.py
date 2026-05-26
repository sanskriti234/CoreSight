# =========================================================
#        CoreSight | Image Folder Scanner & Encoder
# =========================================================
# Scans Images/{roll_no}/ folders
# Generates face encodings if not already present
# Saves encodings in Encodings/{roll_no}.pkl
# =========================================================

import os
import pickle
import numpy as np
import face_recognition
from typing import List
from paths import BASE_DIR,DATASET_DIR,ENCODINGS_DIR,IMAGES_DIR
# ---------------------------------------------------------
# CONFIG (import these from a shared config if you prefer)
# ---------------------------------------------------------

os.makedirs(ENCODINGS_DIR, exist_ok=True)

VALID_IMAGE_EXT = (".jpg", ".jpeg", ".png")


# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
from concurrent.futures import ThreadPoolExecutor

def generate_encoding_for_roll(roll_no: str) -> bool:
    """
    Generates face encoding for a single roll folder.
    Returns True if encoding was generated.
    """

    roll_image_dir = os.path.join(IMAGES_DIR, roll_no)
    encoding_path = os.path.join(ENCODINGS_DIR, f"{roll_no}.pkl")

    # Skip if encoding already exists
    if os.path.exists(encoding_path):
        return False

    if not os.path.isdir(roll_image_dir):
        return False

    # 🔥 Collect image paths (limit to 5 for speed)
    image_files = [
        os.path.join(roll_image_dir, f)
        for f in os.listdir(roll_image_dir)
        if f.lower().endswith(VALID_IMAGE_EXT)
    ][:5]

    def process_image(image_path):
        try:
            image = face_recognition.load_image_file(image_path)

            # 🔥 Skip dark images
            if image.mean() < 20:
                return None

            # 🔥 Resize for faster detection
            small_image = image[::2, ::2]

            locations = face_recognition.face_locations(small_image, model="hog")

            if not locations:
                return None

            # 🔥 Encode using original image
            enc = face_recognition.face_encodings(image)[0]

            return enc

        except Exception as e:
            print(f"[WARN] {roll_no}/{os.path.basename(image_path)}: {e}")
            return None

    # 🔥 Parallel processing
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_image, image_files))

    # 🔥 Filter valid encodings
    encodings = [r for r in results if r is not None]

    # 🔥 Optional: keep only first 3 (faster averaging)
    encodings = encodings[:3]

    if not encodings:
        print(f"[INFO] No valid faces found for {roll_no}")
        return False

    mean_encoding = np.mean(encodings, axis=0)

    with open(encoding_path, "wb") as f:
        pickle.dump(
            {
                "roll_no": roll_no,
                "encoding": mean_encoding
            },
            f
        )

    print(f"[SUCCESS] Encoding generated for {roll_no}")
    return True


def scan_images_and_generate_encodings() -> List[str]:
    """
    Scans Images directory for new roll folders
    Generates encodings for those not yet processed
    Returns list of newly processed roll numbers
    """

    processed = []

    if not os.path.isdir(IMAGES_DIR):
        return processed

    for roll_no in os.listdir(IMAGES_DIR):
        roll_path = os.path.join(IMAGES_DIR, roll_no)

        if not os.path.isdir(roll_path):
            continue

        if generate_encoding_for_roll(roll_no):
            processed.append(roll_no)

    return processed
