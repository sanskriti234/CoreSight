# =========================================================
#                  CoreSight Backend (main.py)
# =========================================================
# Handles student registration, image uploads,
# document generation, and API endpoints for frontend integration.
# =========================================================


import os
import io
import cv2
import json
import pickle
import shutil
import asyncio
import sqlite3
import threading
import numpy as np
import face_recognition
from PIL import Image
from dotenv import load_dotenv
from typing import Optional, List
from docx import Document as DocxDocument
from docx.shared import Inches
from pathlib import Path
import pandas as pd
# Import enhanced DOCX generator
from docx_generator import generate_student_profile_docx, generate_custom_docx, DocxGenerator

from fastapi import (
    FastAPI, File, Form, UploadFile, HTTPException,
    BackgroundTasks, Query
)
from fastapi.responses import (
    JSONResponse, FileResponse, StreamingResponse, HTMLResponse
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from email_service import send_registration_email

from dotenv import load_dotenv
load_dotenv()


# =========================================================
#                  1️⃣ PATH CONFIGURATION
# =========================================================
from paths import BASE_DIR,ATTENDANCE_DIR, ENCODINGS_DIR, IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR,FRONTEND_DIR


# Ensure all essential folders exist
for path in [IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR, ENCODINGS_DIR]:
    os.makedirs(path, exist_ok=True)

# =========================================================
#                  2️⃣ DATABASE CONFIGURATION
# =========================================================

DB_PATH = "Core.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Create students table (if not already)
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    department TEXT,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    academic_year TEXT,
    dob TEXT,
    father_name TEXT,
    father_phone TEXT,
    mother_name TEXT,
    mother_phone TEXT,
    guardian_name TEXT,
    guardian_phone TEXT,
    address TEXT,
    highschool_board TEXT,
    highschool_year TEXT,
    highschool_marks TEXT,
    intermediate_board TEXT,
    intermediate_year TEXT,
    intermediate_marks TEXT,
    diploma TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


'''cursor.execute("""SELECT * FROM students""")
rows = cursor.fetchall()
for row in rows:
    print(row)'''



# =========================================================
#                  4️⃣ FASTAPI INITIALIZATION
# =========================================================

app = FastAPI(title="CoreSight API")

# Static File Mounts
if os.path.isdir(FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

if os.path.isdir(DOCUMENTS_DIR):
    app.mount("/documents", StaticFiles(directory=DOCUMENTS_DIR), name="documents")

if os.path.isdir(IMAGES_DIR):
    app.mount("/static", StaticFiles(directory=IMAGES_DIR), name="static")

# Enable CORS (allow frontend to access backend)
origins = ["http://127.0.0.1:5500", "http://localhost:5500"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
#              CoreSight - Management Module
# =========================================================
from management import router as management_router
app.include_router(management_router)



# =========================================================
#              CoreSight - Attendance Module
# =========================================================
from attendance import router as attendance_router
app.include_router(attendance_router)



# =========================================================
#          CoreSight - Face Recognition Service
# =========================================================
from face_service import (
    router as face_router,
    reload_encodings,
    known_encodings,
    known_rolls
)
app.include_router(face_router)


#=========================================================
#      CoreSight - Manual Face Upload Module (OPTIONAL)
# ========================================================

#        CoreSight | Image Folder Scanner & Encoder
# Scans Images/{roll_no}/ folders
# Generates face encodings if not already present
# Saves encodings in Encodings/{roll_no}.pkl

from encoding_scanner import scan_images_and_generate_encodings

@app.on_event("startup")
def startup_scan():
    new_rolls = scan_images_and_generate_encodings()
    print(f"[STARTUP] New encodings created: {new_rolls}")


# =========================================================
#                  6️⃣ MODELS
# =========================================================
class UserDetails(BaseModel):
    name: str
    roll_no: str
    email: EmailStr
    phone: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    father_name: Optional[str] = None
    father_phone: Optional[str] = None
    mother_name: Optional[str] = None
    mother_phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    highschool_board: Optional[str] = None
    highschool_year: Optional[str] = None
    highschool_marks: Optional[str] = None
    intermediate_board: Optional[str] = None
    intermediate_year: Optional[str] = None
    intermediate_marks: Optional[str] = None
    diploma: Optional[str] = None

# =========================================================
#                  7️⃣ HELPER FUNCTION (Enhanced)
# =========================================================
def generate_profile_files(roll_no: str):
    """Generates a DOCX file and JSON data for a student profile using enhanced generator."""
    json_path = os.path.join(DETAILS_DIR, f"{roll_no}.json")
    if not os.path.exists(json_path):
        print(f"[WARN] JSON not found for {roll_no}")
        return None
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check for profile image
    profile_img_path = os.path.join(IMAGES_DIR, roll_no, "profile.jpg")
    if os.path.exists(profile_img_path):
        data["photo_url"] = f"http://127.0.0.1:8000/static/{roll_no}/profile.jpg"
        image_path = profile_img_path
    else:
        data["photo_url"] = "https://via.placeholder.com/130"
        image_path = None

    # Use enhanced DOCX generator
    doc_path = os.path.join(DOCUMENTS_DIR, f"{roll_no}.docx")
    try:
        generate_student_profile_docx(
            student_data=data,
            image_path=image_path,
            output_path=doc_path
        )
        print(f"[INFO] Generated enhanced DOCX for {roll_no}")
    except Exception as e:
        print(f"[ERROR] Failed to generate DOCX for {roll_no}: {e}")
        return None

    return {"docx": doc_path, "data": data}




# =========================================================
#                  8️⃣ ROUTES
# =========================================================

@app.post("/register-user")
async def register_user(details: UserDetails, background_tasks: BackgroundTasks):
    """Registers a new student and saves details to DB + JSON."""
    user_data = details.model_dump()
    roll_no, email = user_data["roll_no"], user_data["email"]

    cursor.execute("SELECT id FROM students WHERE roll_no=? OR email=?", (roll_no, email))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Roll number or Email already exists")

    cursor.execute("""
        INSERT INTO students (student_name, roll_no, department, email, phone, academic_year, dob,
        father_name, father_phone, mother_name, mother_phone, guardian_name, guardian_phone,
        address, highschool_board, highschool_year, highschool_marks, intermediate_board,
        intermediate_year, intermediate_marks, diploma)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, tuple(user_data.get(k) for k in user_data))
    conn.commit()


    os.makedirs(os.path.join(IMAGES_DIR, roll_no), exist_ok=True)
    with open(os.path.join(DETAILS_DIR, f"{roll_no}.json"), "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4)

    # Reload encoding list if required
    reload_encodings()
    
    # Insert into Excel
    from attendance import add_student_to_existing_attendance

    # add_student_to_existing_attendance(
    #     roll_no=user_data["roll_no"],
    #     name=user_data["name"]
    # )

    # 🔹 Send confirmation email in background
    background_tasks.add_task(
        send_registration_email,
        email=email,
        student_name=user_data["name"],
        roll_no=roll_no,
        department=user_data.get("department")
    )
    
    return {"message": "Student registered successfully", "roll_no": roll_no}


@app.post("/upload-profile-image")
async def upload_profile_image(roll_no: str = Form(...), profile_image: UploadFile = File(...)):
    """Uploads a student's profile image."""
    folder = os.path.join(IMAGES_DIR, roll_no)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "profile.jpg")
    with open(path, "wb") as f:
        f.write(await profile_image.read())
    return {"message": "Profile image uploaded", "path": path}


@app.post("/upload-captured-images")
async def upload_captured_images(roll_no: str = Form(...), images: List[UploadFile] = File(...)):
    """Uploads multiple captured images and generates face encodings."""
    folder = os.path.join(IMAGES_DIR, roll_no)
    os.makedirs(folder, exist_ok=True)

    encodings = []

    for i,img in enumerate(images):
        try:
            contents = await img.read()

            if len(contents) < 5000:
                continue

             # 🔥 SAVE IMAGE (ADD THIS)
            img_path = os.path.join(folder, f"{roll_no}_{i+1}.jpg")
            with open(img_path, "wb") as f:
                f.write(contents)

            # 🔥 DIRECT OpenCV decode (this is the real fix)
            nparr = np.frombuffer(contents, np.uint8)
            img_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img_data is None:
                print("Decode failed")
                continue

            # Convert BGR → RGB
            img_data = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)


            locations = face_recognition.face_locations(img_data,model="cnn")
            
            if locations:
                enc = face_recognition.face_encodings(img_data, locations)[0]
                encodings.append(enc)

        except Exception as e:
            print("Error:", e)
            continue

    if not encodings:
        return {"message": "No valid faces found"}

    mean_enc = np.mean(encodings, axis=0)
    with open(os.path.join(ENCODINGS_DIR, f"{roll_no}.pkl"), "wb") as f:
        pickle.dump({"roll_no": roll_no, "encoding": mean_enc}, f)

    # Reload encodings immediately
    reload_encodings()

    return {"message": "Encodings generated successfully"}



@app.get("/download/{roll_no}")
def download_docx(roll_no: str):
    """Downloads the generated DOCX profile."""
    file_path = os.path.join(DOCUMENTS_DIR, f"{roll_no}.docx")
    if not os.path.exists(file_path):
        result = generate_profile_files(roll_no)
        if not result or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=f"{roll_no}.docx",
                                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/generate-and-preview/{roll_no}", response_class=HTMLResponse)
async def generate_and_preview(roll_no: str):
    """Returns JSON profile data for preview rendering."""
    path = os.path.join(DETAILS_DIR, f"{roll_no}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Profile not found")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    photo_path = os.path.join(IMAGES_DIR, roll_no, "profile.jpg")
    photo_url = f"http://127.0.0.1:8000/static/{roll_no}/profile.jpg" if os.path.exists(photo_path) else "https://via.placeholder.com/130"
    data["photo_url"] = photo_url

    return JSONResponse(content={"status": "success", "data": data})