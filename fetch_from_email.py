#!/usr/bin/env python3

import imaplib
import email
import os
import subprocess
import sys
from datetime import datetime

# ================= CONFIG =================

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

ATTACHMENT_NAME = "data.csv"
SAVE_PATH = "data/tapo_data.csv"

# =========================================

if not GMAIL_USER or not GMAIL_APP_PASSWORD:
    print("❌ ERROR: Missing GMAIL_USER or GMAIL_APP_PASSWORD")
    sys.exit(1)

print("📧 Connecting to Gmail...")

mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
mail.select("inbox")

print("📥 Fetching recent emails...")

status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()[-10:]

if not email_ids:
    print("❌ No emails found")
    mail.logout()
    sys.exit(0)

downloaded = False

for eid in reversed(email_ids):
    status, msg_data = mail.fetch(eid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    subject = msg.get("Subject", "")
    date = msg.get("Date", "")
    print(f"🔍 Checking email: {subject} | {date}")

    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            print(f"📎 Found attachment: {filename}")

            if filename == ATTACHMENT_NAME:
                os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
                with open(SAVE_PATH, "wb") as f:
                    f.write(part.get_payload(decode=True))

                print(f"✅ Downloaded attachment → {SAVE_PATH}")
                downloaded = True
                break

    if downloaded:
        break

mail.logout()

if not downloaded:
    print("❌ Attachment data.csv not found in last 10 emails")
    sys.exit(0)

# ================= GIT PUSH =================

print("📤 Pushing CSV to GitHub...")

subprocess.run(["git", "add", SAVE_PATH], check=True)

commit_msg = f"Update sensor data from email ({datetime.now().isoformat(timespec='seconds')})"
subprocess.run(["git", "commit", "-m", commit_msg], check=False)
subprocess.run(["git", "push"], check=True)

print("🚀 CSV pushed to GitHub successfully")
