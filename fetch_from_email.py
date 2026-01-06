import os
import time
import email
import imaplib
from datetime import datetime
from git import Repo

# ===== CONFIG =====
IMAP_SERVER = "imap.gmail.com"
ATTACHMENT_NAME = "data.csv"
REPO_PATH = os.path.expanduser("~/tapo-dashboard")
CSV_DEST = os.path.join(REPO_PATH, "data", "tapo_data.csv")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
    raise RuntimeError("Missing Gmail environment variables")

# ===== CONNECT TO GMAIL =====
mail = imaplib.IMAP4_SSL(IMAP_SERVER)
mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
mail.select("inbox")

# Search last unread email with attachment
status, messages = mail.search(None, '(UNSEEN)')
email_ids = messages[0].split()

if not email_ids:
    print("No new emails found")
    exit(0)

latest_id = email_ids[-1]
status, msg_data = mail.fetch(latest_id, "(RFC822)")

msg = email.message_from_bytes(msg_data[0][1])

found = False

for part in msg.walk():
    if part.get_content_disposition() == "attachment":
        filename = part.get_filename()
        if filename == ATTACHMENT_NAME:
            with open(CSV_DEST, "wb") as f:
                f.write(part.get_payload(decode=True))
            found = True
            print("CSV downloaded:", CSV_DEST)
            break

if not found:
    print("No data.csv attachment found")
    exit(0)

# ===== COMMIT TO GITHUB =====
repo = Repo(REPO_PATH)
repo.git.add(CSV_DEST)

commit_msg = f"Update sensor data {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
repo.index.commit(commit_msg)
repo.remote(name="origin").push()

print("Data committed and pushed to GitHub")
