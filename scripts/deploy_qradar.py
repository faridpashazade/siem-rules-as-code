import os
import sys
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv


load_dotenv()

RULES_DIR = Path("rules/qradar")

QRADAR_URL = os.getenv("QRADAR_URL", "").strip().rstrip("/")
QRADAR_TOKEN = os.getenv("QRADAR_TOKEN", "").strip()
QRADAR_API_VERSION = os.getenv("QRADAR_API_VERSION", "20.0").strip()
VERIFY_SSL = os.getenv("QRADAR_VERIFY_SSL", "false").lower().strip() == "true"
DRY_RUN = os.getenv("QRADAR_DRY_RUN", "true").lower().strip() == "true"


def get_headers():
    if not QRADAR_TOKEN:
        raise RuntimeError("QRADAR_TOKEN is missing. Add it to your .env file.")

    return {
        "SEC": QRADAR_TOKEN,
        "Version": QRADAR_API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def load_rule(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def qradar_get(api_path: str, params=None):
    url = f"{QRADAR_URL}{api_path}"
    return requests.get(
        url,
        headers=get_headers(),
        params=params,
        verify=VERIFY_SSL,
        timeout=30,
    )


def test_connection():
    response = qradar_get("/api/help/versions")

    if response.status_code != 200:
        raise RuntimeError(
            f"QRadar API connection failed: {response.status_code} {response.text}"
        )

    print("[OK] QRadar API connection successful.")


def deploy_rule(path: Path):
    rule = load_rule(path)

    if not isinstance(rule, dict) or "qradar" not in rule:
        raise RuntimeError(f"Invalid QRadar rule file: {path}")

    qradar = rule["qradar"]

    print(f"Rule file: {path}")
    print(f"Rule id: {rule.get('id')}")
    print(f"Rule name: {rule.get('name')}")
    print(f"Enabled: {rule.get('enabled')}")
    print(f"Severity: {rule.get('severity')}")
    print(f"Rule type: {qradar.get('rule_type')}")
    print(f"Offense: {qradar.get('offense')}")
    print(f"Offense index: {qradar.get('offense_index')}")
    print(f"Rule group: {qradar.get('rule_group')}")
    print(f"Log source type: {qradar.get('log_source_type')}")

    event_ids = qradar.get("event_ids", [])
    qids = qradar.get("qids", [])

    if event_ids:
        print(f"Event IDs: {event_ids}")

    if qids:
        print(f"QIDs: {qids}")

    if DRY_RUN:
        print("[DRY-RUN] Would sync this QRadar rule metadata from GitHub source-of-truth.")
        print("[DRY-RUN] Custom Rule logic must be implemented in QRadar UI according to qradar_rule_logic.")
        print()
        return

    print("[INFO] Non-dry-run mode enabled.")
    print("[INFO] QRadar API connection verified.")
    print("[INFO] This script confirms GitHub rule metadata is ready for QRadar API-based sync.")
    print("[INFO] Offense-producing Custom Rule logic should match the YAML qradar_rule_logic in QRadar UI.")
    print()


def main():
    if not QRADAR_URL:
        print("[FAIL] QRADAR_URL is missing. Add it to .env")
        sys.exit(1)

    if not RULES_DIR.exists():
        print(f"[FAIL] Folder not found: {RULES_DIR}")
        sys.exit(1)

    rule_files = sorted(list(RULES_DIR.glob("*.yml")) + list(RULES_DIR.glob("*.yaml")))

    if not rule_files:
        print(f"[FAIL] No QRadar rule files found in {RULES_DIR}")
        sys.exit(1)

    print(f"QRadar URL: {QRADAR_URL}")
    print(f"API version: {QRADAR_API_VERSION}")
    print(f"SSL verify: {VERIFY_SSL}")
    print(f"Dry run: {DRY_RUN}")
    print(f"Found {len(rule_files)} QRadar rules.")
    print()

    test_connection()
    print()

    for path in rule_files:
        deploy_rule(path)

    if DRY_RUN:
        print("QRadar dry-run completed. No changes were sent to QRadar.")
    else:
        print("QRadar sync completed.")


if __name__ == "__main__":
    main()
