"""
Email service — sends 6-digit OTP verification codes via Gmail SMTP.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings


def _build_html(code: str) -> str:
    """Build a styled HTML email body for the OTP code."""
    return f"""\
    <html>
    <body style="margin:0; padding:0; background:#f4f6f9; font-family:Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
        <tr><td align="center">
          <table width="440" cellpadding="0" cellspacing="0"
                 style="background:#ffffff; border-radius:12px; padding:40px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            <tr><td style="text-align:center;">
              <h2 style="color:#1a1a2e; margin:0 0 8px;">
                Email Verification
              </h2>
              <p style="color:#555; font-size:14px; margin:0 0 28px;">
                Use the code below to verify your email address.
                It expires in <strong>10 minutes</strong>.
              </p>
              <div style="display:inline-block; background:#f0f4ff;
                          border:2px dashed #4361ee; border-radius:8px;
                          padding:16px 36px; letter-spacing:10px;
                          font-size:32px; font-weight:700; color:#4361ee;">
                {code}
              </div>
              <p style="color:#888; font-size:12px; margin:28px 0 0;">
                If you did not request this, please ignore this email.
              </p>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """


def send_verification_email(to_email: str, code: str) -> None:
    """
    Send a 6-digit verification code to `to_email` using Gmail SMTP
    with TLS and App Password authentication.

    Raises smtplib.SMTPException on failure.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Clinical Verify <{settings.email_username}>"
    msg["To"] = to_email
    msg["Subject"] = f"Your verification code: {code}"

    # Plain-text fallback
    plain = f"Your verification code is: {code}\n\nIt expires in 10 minutes."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(_build_html(code), "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.email_username, settings.email_app_password)
        server.sendmail(settings.email_username, to_email, msg.as_string())
