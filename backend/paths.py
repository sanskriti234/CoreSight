from pathlib import Path
import os

# =========================================================
# Base Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

# =========================================================
# Dataset Paths
# =========================================================

DATASET_DIR = BACKEND_DIR / "Dataset"

IMAGES_DIR = DATASET_DIR / "Images"
DETAILS_DIR = DATASET_DIR / "Details"
DOCUMENTS_DIR = DATASET_DIR / "Documents"
ENCODINGS_DIR = DATASET_DIR / "Encodings"
ATTENDANCE_DIR = DATASET_DIR / "Attendance"

# =========================================================
# Frontend Assets
# =========================================================

ASSETS_DIR = FRONTEND_DIR / "assets"

# =========================================================
# Auto-create directories
# =========================================================

DIRECTORIES = [
    DATASET_DIR,
    IMAGES_DIR,
    DETAILS_DIR,
    DOCUMENTS_DIR,
    ENCODINGS_DIR,
    ATTENDANCE_DIR,
    ASSETS_DIR
]

for directory in DIRECTORIES:
    os.makedirs(directory, exist_ok=True)