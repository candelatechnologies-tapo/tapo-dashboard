#!/usr/bin/env python3

import os
import csv
from datetime import datetime
import pytz
from tapo import ApiClient

# ---------------- CONFIG ----------------
TAPO_EMAIL = os.getenv("TAPO_EMAIL")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")
TAPO_DEVICE_IP = os.getenv("TAPO_DEVICE_IP")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

CSV_FILE = "data/tapo_data.csv"

# ---------------- VALIDATION ----------------
if not all([TAPO_EMAIL, TAPO_PASSWORD, TAPO_DEVICE_IP]):
    raise RuntimeError("Missing TAPO_EMAIL / TAPO_PASSWORD / TAPO_DEVICE_IP")

tz = pytz.timezone(TIMEZONE)

# ---------------- FETCH DATA ----------------
async def fetch_data():
    client = ApiClient(TAPO_EMAIL, TAPO_PASSWORD)
    device = await client.p110(TAPO_DEVICE_IP)  # works for T310 sensors

    info = await device.get_device_info()

    temperature = info["current_temp"] / 10.0
    humidity = info["current_humidity"]

    timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    return timestamp, temperature, humidity

# ---------------- WRITE CSV ----------------
def write_csv(row):
    file_exists = os.path.isfile(CSV_FILE)

    os.makedirs("data", exist_ok=True)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "temperature", "humidity"])
        writer.writerow(row)

# ---------------- MAIN ----------------
import asyncio

timestamp, temp, hum = asyncio.run(fetch_data())
write_csv([timestamp, temp, hum])

print(f"✔ {timestamp} | {temp} °C | {hum} %")
