import os
import requests
from dotenv import load_dotenv


load_dotenv()

QRADAR_URL = os.getenv("QRADAR_URL", "").rstrip("/")
QRADAR_TOKEN = os.getenv("QRADAR_TOKEN", "")
QRADAR_API_VERSION = os.getenv("QRADAR_API_VERSION", "20.0")
VERIFY_SSL = os.getenv("QRADAR_VERIFY_SSL", "false").lower() == "true"

if not QRADAR_URL:
    raise SystemExit("[FAIL] QRADAR_URL is missing in .env")

if not QRADAR_TOKEN:
    raise SystemExit("[FAIL] QRADAR_TOKEN is missing in .env")

headers = {
    "SEC": QRADAR_TOKEN,
    "Version": QRADAR_API_VERSION,
    "Accept": "application/json",
}

url = f"{QRADAR_URL}/api/help/versions"

print(f"Testing QRadar connection: {url}")
print(f"API version header: {QRADAR_API_VERSION}")
print(f"SSL verify: {VERIFY_SSL}")

response = requests.get(
    url,
    headers=headers,
    verify=VERIFY_SSL,
    timeout=30,
)

print(f"Status code: {response.status_code}")

if response.status_code == 200:
    print("[OK] QRadar API connection successful.")
    print(response.text[:500])
else:
    print("[FAIL] QRadar API connection failed.")
    print(response.text)
    raise SystemExit(1)
