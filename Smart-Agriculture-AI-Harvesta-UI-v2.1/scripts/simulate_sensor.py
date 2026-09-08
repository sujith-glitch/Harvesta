"""Send clearly labeled synthetic readings to a registered Harvesta sensor device."""

import argparse
import json
import random
import time
from urllib import request


def send_reading(api_url: str, device_uid: str, device_key: str):
    payload = {
        "device_uid": device_uid,
        "soil_moisture": round(random.uniform(36, 58), 1),
        "soil_temperature": round(random.uniform(24, 31), 1),
        "air_temperature": round(random.uniform(27, 35), 1),
        "air_humidity": round(random.uniform(48, 76), 1),
        "soil_ph": round(random.uniform(6.2, 7.1), 2),
        "nitrogen": round(random.uniform(35, 90), 1),
        "phosphorus": round(random.uniform(18, 55), 1),
        "potassium": round(random.uniform(28, 80), 1),
        "rainfall": 0.0,
        "battery_level": round(random.uniform(82, 100), 1),
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{api_url.rstrip('/')}/api/sensors/ingest",
        data=body,
        headers={"Content-Type": "application/json", "X-Device-Key": device_key},
        method="POST",
    )
    with request.urlopen(req, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    reading = result["reading"]
    print(f"Accepted synthetic reading #{reading['id']} at {reading['recorded_at']}")


def main():
    parser = argparse.ArgumentParser(description="Harvesta synthetic sensor simulator (development only)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--device-uid", required=True)
    parser.add_argument("--device-key", required=True)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    print("DEVELOPMENT SIMULATOR: these values are synthetic and are not physical farm measurements.")
    while True:
        send_reading(args.api_url, args.device_uid, args.device_key)
        if args.once:
            break
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    main()
