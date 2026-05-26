from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BACKEND_DIR = BASE_DIR / "backend"
DATASET_DIR = BACKEND_DIR / "Dataset"
FRONTEND_DIR = BASE_DIR / "frontend"

IMAGES_DIR = DATASET_DIR / "Images"
DETAILS_DIR = DATASET_DIR / "Details"
DOCUMENTS_DIR = DATASET_DIR / "Documents"
ENCODINGS_DIR = DATASET_DIR / "Encodings"
ATTENDANCE_DIR = DATASET_DIR / "Attendance"
