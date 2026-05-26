# =========================================================
#              CoreSight - Attendance Module
# =========================================================

import os
import sqlite3
import calendar
import numpy as np
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from PIL import Image
import io
from paths import BASE_DIR,ATTENDANCE_DIR, ENCODINGS_DIR, IMAGES_DIR, DETAILS_DIR, DOCUMENTS_DIR,FRONTEND_DIR


# 🔗 IMPORT SHARED FACE DATA
from face_service import known_encodings, known_rolls

# =========================================================
# Router
# =========================================================
router = APIRouter(prefix="/attendance", tags=["Attendance"])

os.makedirs(ATTENDANCE_DIR, exist_ok=True)

DB_PATH = "Core.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# =========================================================
# Attendance Log Table
# =========================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    date TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# =========================================================
#               Insert into excel
# =========================================================


from openpyxl import load_workbook
import calendar
from datetime import datetime

def add_student_to_existing_attendance(roll_no: str, name: str):
    year = datetime.now().year
    file_path = os.path.join(ATTENDANCE_DIR, f"Attendance-{year}.xlsx")

    if not os.path.exists(file_path):
        return  # Attendance not created yet

    wb = load_workbook(file_path)
    ws = wb.active

    for month in range(1, 13):
        month_header = f"{calendar.month_name[month].upper()} {year}"

        header_row = None
        for r in range(1, ws.max_row + 1):
            if ws.cell(r, 1).value == month_header:
                header_row = r
                break

        if not header_row:
            continue

        # find insertion row (before blank gap)
        r = header_row + 2
        while ws.cell(r, 1).value:
            r += 1

        ws.cell(r, 1, roll_no)
        safe_write(ws, r, 2, name)

        days = calendar.monthrange(year, month)[1]
        start = chr(ord("C"))
        end = chr(ord("C") + days - 1)

        ws.cell(r, 3 + days, f'=COUNTIF({start}{r}:{end}{r},"P")')
        ws.cell(r, 4 + days, f'=COUNTIF({start}{r}:{end}{r},"A")')
        ws.cell(r, 5 + days, f'=IF({3+days}{r}=0,0,{3+days}{r}*100/{days})')

    wb.save(file_path)

def safe_write(ws, row, col, value):
    cell = ws.cell(row=row, column=col)

    for merged_range in ws.merged_cells.ranges:
        if cell.coordinate in merged_range:
            top_left = ws.cell(
                row=merged_range.min_row,
                column=merged_range.min_col
            )
            top_left.value = value
            return

    cell.value = value


# =========================================================
#               Helpers
# =========================================================
def already_marked_today(roll_no: str):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT id FROM attendance_log WHERE roll_no=? AND date=?",
        (roll_no, today)
    )
    return cursor.fetchone() is not None


def insert_attendance_log(roll_no: str):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO attendance_log (roll_no, date) VALUES (?, ?)",
        (roll_no, today)
    )
    conn.commit()

def ensure_attendance_excel_exists(year: int):
    file_path = os.path.join(ATTENDANCE_DIR, f"Attendance-{year}.xlsx")
    
    print("[DEBUG] Attendance Excel path:", file_path)

    if os.path.exists(file_path):
        return  # already exists

    print(f"[AUTO] Attendance Excel missing. Generating Attendance-{year}.xlsx")

    # --- Generate new workbook ---
    wb = Workbook()
    ws = wb.active
    ws.title = f"{year}-Attendance"

    cursor.execute("SELECT student_name, roll_no FROM students ORDER BY roll_no")
    students = cursor.fetchall()

    row = 1
    for month_index in range(1, 13):
        month = calendar.month_name[month_index]
        days = calendar.monthrange(year, month_index)[1]

        # Month header
        ws.merge_cells(
            start_row=row,
            start_column=1,
            end_row=row,
            end_column=days + 5
        )
        ws.cell(row, 1, f"{month.upper()} {year}")
        row += 1

        # Table header
        ws.append(
            ["Roll No", "Name"] +
            list(range(1, days + 1)) +
            ["Total P", "Total A", "%"]
        )
        row += 1

        # Student rows
        for name, roll in students:
            ws.cell(row, 1, roll)
            ws.cell(row, 2, name)

            start = get_column_letter(3)
            end = get_column_letter(2 + days)
            total_p = get_column_letter(3 + days)

            ws.cell(row, 3 + days,
                    f'=COUNTIF({start}{row}:{end}{row},"P")')
            ws.cell(row, 4 + days,
                    f'=COUNTIF({start}{row}:{end}{row},"A")')
            ws.cell(row, 5 + days,
                    f'=IF({total_p}{row}=0,0,{total_p}{row}*100/{days})')

            row += 1

        row += 3  # gap before next month

    wb.save(file_path)
    print(f"[AUTO] Attendance-{year}.xlsx generated successfully")


def mark_attendance_in_excel(roll_no: str):
    now = datetime.now()
    year, month, day = now.year, now.month, now.day
    
    # ✅ AUTO-GENERATE if missing
    ensure_attendance_excel_exists(year)
    file_path = os.path.join(ATTENDANCE_DIR, f"Attendance-{year}.xlsx")
    
    wb = load_workbook(file_path)
    ws = wb.active

    month_header = f"{calendar.month_name[month].upper()} {year}"

    header_row = None
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 1).value == month_header:
            header_row = r
            break

    if not header_row:
        raise Exception("Month block not found")

    r = header_row + 2
    while ws.cell(r, 1).value:
        if str(ws.cell(r, 1).value).strip() == roll_no:
            ws.cell(r, 2 + day, "P")
            wb.save(file_path)
            return
        r += 1

    raise Exception("Student not found in attendance sheet")

# =========================================================
#       Generate Attendance Register
# =========================================================
@router.get("/generate-register/{year}")
def generate_attendance_register(year: int):
    wb = Workbook()
    ws = wb.active
    ws.title = f"{year}-Attendance"

    cursor.execute("SELECT student_name, roll_no FROM students ORDER BY roll_no")
    students = cursor.fetchall()

    row = 1
    for month_index in range(1, 13):
        month = calendar.month_name[month_index]
        days = calendar.monthrange(year, month_index)[1]

        ws.merge_cells(
            start_row=row,
            start_column=1,
            end_row=row,
            end_column=days + 5
    
        )
        ws.cell(row, 1, f"{month.upper()} {year}")
        row += 1

        ws.append(["Roll No", "Name"] + list(range(1, days + 1)) + ["Total P", "Total A", "%"])
        row += 1

        for name, roll in students:
            ws.cell(row, 1, roll)
            ws.cell(row, 2, name)

            start = get_column_letter(3)
            end = get_column_letter(2 + days)
            total_p = get_column_letter(3 + days)

            ws.cell(row, 3 + days, f'=COUNTIF({start}{row}:{end}{row},"P")')
            ws.cell(row, 4 + days, f'=COUNTIF({start}{row}:{end}{row},"A")')
            ws.cell(row, 5 + days, f'=IF({total_p}{row}=0,0,{total_p}{row}*100/{days})')

            row += 1

        row += 3

    file_path = os.path.join(ATTENDANCE_DIR, f"Attendance-{year}.xlsx")
    wb.save(file_path)

    return FileResponse(file_path, filename=os.path.basename(file_path))

# =========================================================
#               Face-based Attendance 
# =========================================================
@router.post("/mark-by-face")
async def mark_attendance_by_face(frame: UploadFile = File(...)):
    image_bytes = await frame.read()
    image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))

    if not known_encodings:
        return {"status": "no_encodings_loaded"}

    import face_recognition
    encs = face_recognition.face_encodings(image)
    if not encs:
        return {"status": "no_face"}

    distances = face_recognition.face_distance(known_encodings, encs[0])
    best = np.argmin(distances)

    if distances[best] >= 0.45:
        return {"status": "unknown"}

    roll_no = known_rolls[best]

    if already_marked_today(roll_no):
        return {"status": "already_marked", "roll_no": roll_no}

    mark_attendance_in_excel(roll_no)
    insert_attendance_log(roll_no)

    return {"status": "marked_present", "roll_no": roll_no}

# =========================================================
#                 Today's Logs
# =========================================================
@router.get("/logs-today")
def attendance_logs_today():
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT roll_no, time(timestamp)
        FROM attendance_log
        WHERE date=?
        GROUP BY roll_no
        ORDER BY timestamp DESC
    """, (today,))

    return {
        "logs": [
            {"roll_no": r[0], "time": r[1], "status": "Present"}
            for r in cursor.fetchall()
        ]
    }


