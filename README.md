# CoreSight  
### AI-Based Face Recognition & Attendance System

CoreSight is a **production-oriented, modular AI system** built for **student identity management, real-time face recognition, automated attendance tracking, and document generation**.  
The project demonstrates **applied computer vision, backend engineering, and full-stack integration**, making it suitable for **internships, research projects, and real-world deployments**.

---

## 🎯 Project Objectives

- Automate student identification using AI-based face recognition
- Eliminate manual attendance processes
- Maintain secure and structured student records
- Demonstrate scalable backend architecture
- Provide deployment-ready full-stack solution

---

## 🚀 Key Capabilities

- AI-powered face recognition (dlib-based)
- Student registration & profile management
- Real-time attendance marking
- Modular FastAPI backend
- Auto-generated student documents (DOCX)
- SQLite persistence (cloud-upgradable)
- Frontend dashboard with live recognition
- Clean separation of services

---

## 🧠 Technology Stack

### Backend
- Python 3.10+
- FastAPI
- OpenCV
- face_recognition (dlib)
- SQLite (Production-ready for small scale)
- NumPy, Pillow
- python-docx
- Uvicorn

### Frontend
- HTML5
- CSS3
- JavaScript
- Web Camera API

---

## 🏗️ System Architecture

Frontend (Browser)
│
│ REST API Calls
▼
FastAPI Backend
│
├── Face Recognition Service
├── Attendance Service
├── Document Generator
├── Email Service
│
▼
SQLite Database + File Storage

---

## 📁 Project Structure

CoreSight/
│
├── backend/
│ ├── Dataset/
│ │ ├── Attendance/
│ │ ├── Details/
│ │ ├── Documents/
│ │ ├── Encodings/
│ │ └── Images/
│ │
│ ├── attendance.py
│ ├── docx_generator.py
│ ├── email_service.py
│ ├── encoding_scanner.py
│ ├── face_service.py
│ ├── management.py
│ ├── models.py
│ ├── paths.py
│ ├── recognize.py
│ └── main.py
│
├── frontend/
│ ├── dashboard.html
│ ├── face_recognition.html
│ ├── StudentRegistration.html
│ ├── attendance.html
│ └── preview.html
│
└── README.md


---

## ⚙️ Local Setup

### 1️⃣ Clone Repository
```bash
git clone https://github.com/your-username/CoreSight.git
cd CoreSight

2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt


If requirements.txt is missing, generate using:

pip freeze > requirements.txt

4️⃣ Run Application
uvicorn backend.main:app --host 0.0.0.0 --port 8000


Access:

http://127.0.0.1:8000

🌐 Frontend Usage


| Page                     | Purpose            |
| ------------------------ | ------------------ |
| dashboard.html           | System overview    |
| StudentRegistration.html | Student onboarding |
| CaptureImage.html        | Face data capture  |
| face_recognition.html    | Live recognition   |
| attendance.html          | Attendance records |
| preview.html             | Profile preview    |


🧪 API Overview

| Method | Endpoint                | Description             |
| ------ | ----------------------- | ----------------------- |
| POST   | /register-user          | Register student        |
| POST   | /upload-captured-images | Generate face encodings |
| POST   | /recognize-faces        | Recognize face          |
| GET    | /attendance             | Fetch attendance        |
| GET    | /download/{roll_no}     | Download DOCX           |


🛡️ Security & Privacy Considerations

- No third-party face APIs used
- All biometric data stored locally
- Environment variable support
- Easily extendable to encrypted storage

🚀 Deployment Guide


📈 Scalability Notes

- SQLite → PostgreSQL (production)
- Local images → AWS S3 / Cloud Storage
- Single server → Kubernetes-ready
- Can integrate CCTV feeds


🌱 Future Enhancements

- Role-based authentication
- Mobile app
- Cloud face indexing
- Attendance analytics
- Live classroom integration

👨‍💻 Author

CoreSight
AI & Computer Vision Project


📜 License

Educational and demonstration use only.
Commercial usage requires authorization.

⭐ Star the repository if this project helped you.