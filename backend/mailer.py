import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_interview_email(doctor_id: str, to_email: str = "yassine.alikacem@gmail.com"):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "khelfat.takieddine@gmail.com"
    sender_password = os.getenv("SMTP_APP_PASSWORD")

    if not sender_password:
        print("[!] Cannot send email: SMTP_APP_PASSWORD not set in .env")
        return

    interview_link = f"http://localhost:5173/interview/{doctor_id}"

    subject = "Action Required: Your Clinical Identity AI Interview is Ready"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1e3a8a;">Clinical Identity Verification</h2>
        <p>Dear Doctor,</p>
        <p>Your documents have been successfully processed and verified.</p>
        <p>You are now required to complete a short, automated voice and video interview to finalize your verification.</p>
        <div style="margin: 30px 0;">
            <a href="{interview_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Start AI Interview
            </a>
        </div>
        <p>Or copy this link into your browser:</p>
        <p><a href="{interview_link}">{interview_link}</a></p>
        <br>
        <p>Best regards,<br>The Verification Team</p>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    msg.attach(MIMEText(body, "html"))

    print(f"[MAILER] Sending email to {to_email} via {smtp_server}...")
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"[+] Email successfully sent to {to_email}!")
    except Exception as e:
        print(f"[-] Failed to send email: {e}")

if __name__ == "__main__":
    # Test script
    import sys
    test_id = sys.argv[1] if len(sys.argv) > 1 else "test_123"
    send_interview_email(test_id)
