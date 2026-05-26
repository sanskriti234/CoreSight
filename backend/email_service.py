# =========================================================
#           Email Service Module (email_service.py)
# =========================================================

import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="D:/CoreSight/.env")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_SENDER,
    MAIL_PASSWORD=EMAIL_PASSWORD,
    MAIL_FROM=EMAIL_SENDER,
    MAIL_FROM_NAME="CoreSight Support",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(conf)


async def send_registration_email(
    email: str,
    student_name: str,
    roll_no: str,
    department: str | None = None
):
    """
    Sends registration confirmation email to student
    """

    subject = "🎓 CoreSight Registration Successful"

    body = f"""
    Dear {student_name},

    Congratulations! Your registration with CoreSight has been completed successfully.

    📌 Registration Details:
    ---------------------------------
    Name       : {student_name}
    Roll No    : {roll_no}
    Department : {department or "N/A"}

    You can now proceed with:
    • Image upload
    • Face recognition enrollment
    • Attendance tracking

    If you did not perform this registration, please contact support immediately.

    Regards,
    CoreSight Team
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="plain"
    )

    await fast_mail.send_message(message)
