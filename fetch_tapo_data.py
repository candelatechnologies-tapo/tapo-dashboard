import os
import csv
import pytz
import pandas as pd
from datetime import datetime
from tapo import ApiClient

# =========================
# USER CONFIG
# =========================
TAPO_EMAIL = "YOUR_TAPO_EMAIL"
TAPO_PASSWORD = "YOUR_TAPO_PASSWORD"
DEVICE_IP = "YOUR_T310_IP"     # Optional, not required for cloud
TIMEZONE = "Asia/Kolkata"      # Change if needed

CSV_PATH = "data/tapo_data.csv"

# =========================
# INIT
# =========================
tz = pytz.timezone(TIMEZONE)
now = datetime.now(tz)

# =========================
# CONNECT TO TAPO CLOUD
# =========================
client = ApiClient(TAPO_EMAIL, TAPO_PASSWORD)
device = client.get_device(DEVICE_IP)

# =========================
# FETCH RAW DATA (per-minute)
# =========================
print("Fetching sensor data from Tapo cloud...")

history = device.get_temperature_humidity_records(
    start_date=now.replace(hour=0, minute=0, second=0),
    end_date=now
)

if not history:
    print("No data received from sensor.")
    exit(0)

df = pd.DataFrame(history)

# Expected keys from Tapo:
# time, temperature, humidity
df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(pytz.UTC).dt.tz_convert(tz)
df["temperature"] = df["temperature"].astype(float)
df["humidity"] = df["humidity"].astype(float)

# =========================
# AGGREGATE PER HOUR
# =========================
df["hour"] = df["time"].dt.floor("H")

hourly = (
    df.groupby("hour")
    .agg({
        "temperature": "mean",
        "humidity": "mean"
    })
    .reset_index()
)

# =========================
# LOAD EXISTING CSV (if any)
# =========================
existing_hours = set()

if os.path.exists(CSV_PATH):
    existing_df = pd.read_csv(CSV_PATH)
    existing_df["hour"] = pd.to_datetime(existing_df["timestamp"])
    existing_hours = set(existing_df["hour"].astype(str))

# =========================
# APPEND NEW HOURS ONLY
# =========================
new_rows = []

for _, row in hourly.iterrows():
    ts = row["hour"].strftime("%Y-%m-%d %H:%M")
    if ts in existing_hours:
        continue

    new_rows.append([
        ts,
        round(row["temperature"], 2),
        round(row["humidity"], 2)
    ])

if not new_rows:
    print("No new hourly data to append.")
    exit(0)

# =========================
# WRITE CSV
# =========================
os.makedirs("data", exist_ok=True)
file_exists = os.path.exists(CSV_PATH)

with open(CSV_PATH, "a", newline="") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow(["timestamp", "temperature", "humidity"])

    writer.writerows(new_rows)

print(f"Appended {len(new_rows)} new hourly records to {CSV_PATH}")
