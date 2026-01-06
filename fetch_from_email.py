import imaplib
import email
import os
import subprocess
from datetime import datetime

# ================= CONFIG =================
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

ATTACHMENT_NAME = "data.csv"
SAVE_PATH = "data/tapo_data.csv"

# ================= SANITY CHECK =================
print("🔍 Checking environment variables...")

if not GMAIL_USER or not GMAIL_APP_PASSWORD:
    print("❌ GMAIL_USER or GMAIL_APP_PASSWORD not set")
    exit(1)

print("✅ Environment variables OK")

# ================= CONNECT =================
print("📧 Connecting to Gmail IMAP...")
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
print("✅ Logged into Gmail")

mail.select("inbox")

# ================= SEARCH =================
print("🔎 Searching for emails with attachments...")
status, data = mail.search(None, 'ALL')

email_ids = data[0].split()
print(f"📬 Total emails found: {len(email_ids)}")

if not email_ids:
    print("❌ No emails in inbox")
    exit(0)

# ================= FETCH LATEST EMAIL FIRST =================
downloaded = False

for eid in reversed(email_ids):
    status, msg_data = mail.fetch(eid, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    subject = msg.get("Subject", "")
    print(f"\n📨 Checking email: {subject}")

    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            print(f"📎 Found attachment: {filename}")

            if filename == ATTACHMENT_NAME:
                print("✅ Matching attachment found")

                os.makedirs("data", exist_ok=True)

                with open(SAVE_PATH, "wb") as f:
                    f.write(part.get_payload(decode=True))

                print(f"💾 Saved attachment to {SAVE_PATH}")
                downloaded = True
                break

    if downloaded:
        break

mail.logout()

if not downloaded:
    print("❌ No matching attachment found (data.csv)")
    exit(0)

# ================= GIT PUSH =================
print("📤 Committing to GitHub...")

subprocess.run(["git", "add", SAVE_PATH], check=True)
subprocess.run([
    "git",
    "commit",
    "-m",
    f"Update sensor data {datetime.now().isoformat()}"
], check=True)

subprocess.run(["git", "push"], check=True)

print("🚀 CSV pushed to GitHub successfully")
