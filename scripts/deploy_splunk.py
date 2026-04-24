import os
import sys
from pathlib import Path
from urllib.parse import quote

import requests
import yaml
from dotenv import load_dotenv


load_dotenv()

RULES_DIR = Path("rules/splunk")

SPLUNK_URL = os.getenv("SPLUNK_URL", "").rstrip("/")
SPLUNK_TOKEN = os.getenv("SPLUNK_TOKEN", "")
SPLUNK_AUTH_SCHEME = os.getenv("SPLUNK_AUTH_SCHEME", "Bearer")
DEFAULT_APP = os.getenv("SPLUNK_APP", "search")
DEFAULT_OWNER = os.getenv("SPLUNK_OWNER", "nobody")
VERIFY_SSL = os.getenv("SPLUNK_VERIFY_SSL", "false").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def load_rule(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_headers():
    if not SPLUNK_TOKEN:
        raise RuntimeError("SPLUNK_TOKEN is missing. Add it to your .env file.")

    return {
        "Authorization": f"{SPLUNK_AUTH_SCHEME} {SPLUNK_TOKEN}",
    }


def build_payload(rule: dict):
    splunk = rule["splunk"]

    return {
        "name": rule["name"],
        "search": splunk["search"],
        "description": rule.get("description", ""),
        "disabled": "0" if rule.get("enabled", True) else "1",
        "is_scheduled": "1",
        "cron_schedule": splunk.get("cron_schedule", "*/5 * * * *"),
        "dispatch.earliest_time": splunk.get("earliest_time", "-5m"),
        "dispatch.latest_time": splunk.get("latest_time", "now"),
        "alert_type": splunk.get("alert_type", "number of events"),
        "alert_comparator": splunk.get("alert_comparator", "greater than"),
        "alert_threshold": str(splunk.get("alert_threshold", 0)),
        "output_mode": "json",
    }


def splunk_request(method, url, **kwargs):
    return requests.request(
        method=method,
        url=url,
        headers=get_headers(),
        verify=VERIFY_SSL,
        timeout=30,
        **kwargs,
    )


def deploy_rule(path: Path):
    rule = load_rule(path)

    if not isinstance(rule, dict) or "splunk" not in rule:
        raise RuntimeError(f"Invalid rule file: {path}")

    splunk = rule["splunk"]

    name = rule["name"]
    app = splunk.get("app", DEFAULT_APP)
    owner = splunk.get("owner", DEFAULT_OWNER)

    base_url = f"{SPLUNK_URL}/servicesNS/{owner}/{app}/saved/searches"
    saved_search_url = f"{base_url}/{quote(name, safe='')}"

    payload = build_payload(rule)

    print(f"Rule file: {path}")
    print(f"Rule name: {name}")
    print(f"Target app: {app}")
    print(f"Target owner: {owner}")

    if DRY_RUN:
        print("[DRY-RUN] Would check saved search:")
        print(f"          GET {saved_search_url}")
        print("[DRY-RUN] Would create/update with this payload:")
        print(f"          name={payload['name']}")
        print(f"          cron_schedule={payload['cron_schedule']}")
        print(f"          earliest_time={payload['dispatch.earliest_time']}")
        print(f"          latest_time={payload['dispatch.latest_time']}")
        print()
        return

    if not SPLUNK_URL:
        raise RuntimeError("SPLUNK_URL is missing. Add it to your .env file.")

    check_response = splunk_request("GET", saved_search_url, params={"output_mode": "json"})

    if check_response.status_code == 200:
        print(f"[UPDATE] Existing Splunk saved search found: {name}")

        update_payload = payload.copy()
        update_payload.pop("name", None)

        response = splunk_request(
            "POST",
            saved_search_url,
            data=update_payload,
        )

    elif check_response.status_code == 404:
        print(f"[CREATE] Splunk saved search not found. Creating: {name}")

        response = splunk_request(
            "POST",
            base_url,
            data=payload,
        )

    else:
        raise RuntimeError(
            f"Splunk lookup failed for {name}: "
            f"{check_response.status_code} {check_response.text}"
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Splunk deploy failed for {name}: "
            f"{response.status_code} {response.text}"
        )

    print(f"[OK] Deployed: {name}")
    print()


def main():
    if not RULES_DIR.exists():
        print(f"[FAIL] Folder not found: {RULES_DIR}")
        sys.exit(1)

    rule_files = sorted(list(RULES_DIR.glob("*.yml")) + list(RULES_DIR.glob("*.yaml")))

    if not rule_files:
        print(f"[FAIL] No rule files found in {RULES_DIR}")
        sys.exit(1)

    print(f"Splunk URL: {SPLUNK_URL if SPLUNK_URL else 'NOT SET'}")
    print(f"Auth scheme: {SPLUNK_AUTH_SCHEME}")
    print(f"SSL verify: {VERIFY_SSL}")
    print(f"Dry run: {DRY_RUN}")
    print(f"Found {len(rule_files)} rules.\n")

    for path in rule_files:
        deploy_rule(path)

    if DRY_RUN:
        print("Dry-run completed. No changes were sent to Splunk.")
    else:
        print("Splunk deployment completed.")


if __name__ == "__main__":
    main()
