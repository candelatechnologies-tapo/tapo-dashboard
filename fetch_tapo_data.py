import os
import csv
import pytz
import pandas as pd
from datetime import datetime, timedelta
from tapo import ApiClient

# =========================
# READ FROM GITHUB SECRETS
# =========================
TAPO_EMAIL = os.environ["TAPO_EMAIL"]
TAPO_PASSWORD = os.environ["TAPO_PASSWORD"]
DEVICE_IP = os.environ.get("TAPO_DEVICE_IP", "")
TIMEZONE = os.environ.get("TIMEZONE", "UTC")

CSV_PATH = "data/tapo_data.csv"

tz = pytz.timezone(TIMEZONE)
now = datetime.now(tz)

print("Connecting to Tapo Cloud...")

client = ApiClient(TAPO_EMAIL, TAPO_PASSWORD)
device = client.get_device(DEVICE_IP)

# =========================
# FETCH LAST 24 HOURS
# =========================
start_time = now - timedelta(hours=24)

records = device.get_temperature_humidity_records(
    start_date=start_time,
    end_date=now
)

if not records:
    print("No data received.")
    exit(0)

df = pd.DataFrame(records)

df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert(tz)
df["temperature"] = df["temperature"].astype(float)
df["humidity"] = df["humidity"].astype(float)

# =========================
# HOURLY AVERAGE
# =========================
df["hour"] = df["time"].dt.floor("H")

hourly = (
    df.groupby("hour")
    .agg({"temperature": "mean", "humidity": "mean"})
    .reset_index()
)

# =========================
# LOAD EXISTING CSV
# =========================
existing_hours = set()

if os.path.exists(CSV_PATH):
    old = pd.read_csv(CSV_PATH)
    old["timestamp"] = pd.to_datetime(old["timestamp"])
    existing_hours = set(old["timestamp"].dt.strftime("%Y-%m-%d %H:%M"))

# =========================
# APPEND NEW HOURS
# =========================
new_rows = []

for _, r in hourly.iterrows():
    ts = r["hour"].strftime("%Y-%m-%d %H:%M")
    if ts in existing_hours:
        continue

    new_rows.append([
        ts,
        round(r["temperature"], 2),
        round(r["humidity"], 2)
    ])

if not new_rows:
    print("No new hourly data to append.")
    exit(0)

os.makedirs("data", exist_ok=True)
file_exists = os.path.exists(CSV_PATH)

with open(CSV_PATH, "a", newline="") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["timestamp", "temperature", "humidity"])
    writer.writerows(new_rows)

print(f"Added {len(new_rows)} new hourly rows.")
