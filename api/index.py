from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="NextHire Waitlist API")

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production e.g. ["https://nexthire.com"]
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── CONFIG (set these in Vercel Environment Variables) ────────────
SMTP_HOST    = "smtp.gmail.com"
SMTP_PORT    = 587
GMAIL_USER   = os.environ.get("GMAIL_USER")
GMAIL_PASS   = os.environ.get("GMAIL_PASS")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "arshadmsb@gmail.com")


# ── SCHEMA ────────────────────────────────────────────────────────
class WaitlistEntry(BaseModel):
    email: EmailStr


# ── EMAIL SENDER ──────────────────────────────────────────────────
def send_notification(signup_email: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚀 New NextHire Waitlist Signup"
    msg["From"]    = GMAIL_USER
    msg["To"]      = NOTIFY_EMAIL

    time_now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    html = f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:520px;margin:0 auto;background:#080C14;border-radius:16px;overflow:hidden;border:1px solid #1E2D44;">
      <div style="background:linear-gradient(135deg,#00C6A7,#1A6FFF);padding:3px 0;"></div>
      <div style="padding:36px 40px;">
        <h1 style="font-size:1.4rem;color:#E8EFF9;margin:0 0 6px;letter-spacing:-0.02em;">New Waitlist Signup</h1>
        <p style="color:#6B82A3;font-size:0.85rem;margin:0 0 28px;">Someone just joined the NextHire waitlist</p>

        <div style="background:#0F1A28;border:1px solid #1E2D44;border-radius:10px;padding:20px 24px;margin-bottom:16px;">
          <p style="margin:0 0 6px;font-size:0.7rem;color:#6B82A3;letter-spacing:0.1em;text-transform:uppercase;font-family:monospace;">Signup Email</p>
          <p style="margin:0;font-size:1.1rem;color:#00C6A7;font-weight:600;">{signup_email}</p>
        </div>

        <div style="background:#0F1A28;border:1px solid #1E2D44;border-radius:10px;padding:20px 24px;">
          <p style="margin:0 0 6px;font-size:0.7rem;color:#6B82A3;letter-spacing:0.1em;text-transform:uppercase;font-family:monospace;">Timestamp</p>
          <p style="margin:0;font-size:0.95rem;color:#E8EFF9;">{time_now}</p>
        </div>

        <p style="margin:28px 0 0;font-size:0.8rem;color:#3A506B;font-family:monospace;">// NextHire Waitlist System</p>
      </div>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())


# ── ROUTES ────────────────────────────────────────────────────────
@app.get("/api")
def root():
    return {"status": "NextHire Waitlist API is running ✅"}


@app.post("/api/notify")
def notify(entry: WaitlistEntry):
    if not GMAIL_USER or not GMAIL_PASS:
        raise HTTPException(status_code=500, detail="Email credentials not configured")
    try:
        send_notification(entry.email)
        return {"success": True, "message": "Notification sent"}
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="Gmail auth failed — check GMAIL_USER and GMAIL_PASS in Vercel env vars")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
