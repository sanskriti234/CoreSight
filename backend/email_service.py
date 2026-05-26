# =========================================================
#           Email Service Module (email_service.py)
# =========================================================

import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_SENDER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_SENDER"),
    MAIL_FROM_NAME="CoreSight Support"
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
