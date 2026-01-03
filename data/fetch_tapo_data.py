import os
import csv
import asyncio
from datetime import datetime
from tapo import ApiClient

OUTPUT_CSV = "data/tapo_data.csv"

async def main():
    email = os.environ["TAPO_EMAIL"]
    password = os.environ["TAPO_PASSWORD"]
    ip = os.environ["T310_IP"]

    client = ApiClient(email, password)
    device = await client.t310(ip)

    # Pull records from the sensor (library returns a list/dicts)
    records = await device.get_temperature_humidity_records()

    rows = []
    for r in records:
        ts = datetime.fromtimestamp(r["timestamp"])
        rows.append([
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            r["temperature"],
            r["humidity"],
        ])

    # Write CSV
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Timestamp", "Temperature_C", "Humidity_percent"])
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")

asyncio.run(main())

