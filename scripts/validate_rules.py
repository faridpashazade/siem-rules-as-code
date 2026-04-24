import sys
from pathlib import Path

import yaml


RULES_DIR = Path("rules/splunk")

REQUIRED_TOP_LEVEL_FIELDS = [
    "id",
    "name",
    "description",
    "enabled",
    "severity",
    "splunk",
]

REQUIRED_SPLUNK_FIELDS = [
    "app",
    "owner",
    "search",
    "cron_schedule",
    "earliest_time",
    "latest_time",
    "alert_type",
    "alert_comparator",
    "alert_threshold",
]

VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validate_rule(path: Path):
    errors = []

    try:
        rule = load_yaml(path)
    except Exception as error:
        return [f"YAML parse error: {error}"]

    if not isinstance(rule, dict):
        return ["Rule file is empty or invalid YAML object."]

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in rule:
            errors.append(f"Missing top-level field: {field}")

    severity = str(rule.get("severity", "")).lower()
    if severity and severity not in VALID_SEVERITIES:
        errors.append(f"Invalid severity: {rule.get('severity')}")

    splunk = rule.get("splunk")
    if not isinstance(splunk, dict):
        errors.append("splunk field must be an object.")
        return errors

    for field in REQUIRED_SPLUNK_FIELDS:
        if field not in splunk:
            errors.append(f"Missing splunk field: {field}")

    search = splunk.get("search", "")
    if not isinstance(search, str) or not search.strip():
        errors.append("splunk.search is empty.")

    if isinstance(search, str):
        stripped_search = search.strip()
        if not stripped_search.startswith(("index=", "|")):
            errors.append("splunk.search should usually start with index= or |.")

    return errors


def main():
    if not RULES_DIR.exists():
        print(f"[FAIL] Folder not found: {RULES_DIR}")
        sys.exit(1)

    rule_files = sorted(list(RULES_DIR.glob("*.yml")) + list(RULES_DIR.glob("*.yaml")))

    if not rule_files:
        print(f"[FAIL] No YAML files found in {RULES_DIR}")
        sys.exit(1)

    seen_ids = {}
    seen_names = {}
    failed = False

    print(f"Found {len(rule_files)} Splunk rule files.\n")

    for path in rule_files:
        print(f"Checking: {path}")
        errors = validate_rule(path)

        try:
            rule = load_yaml(path)
        except Exception:
            rule = {}

        rule_id = rule.get("id") if isinstance(rule, dict) else None
        rule_name = rule.get("name") if isinstance(rule, dict) else None

        if rule_id:
            if rule_id in seen_ids:
                errors.append(f"Duplicate id: {rule_id} also used in {seen_ids[rule_id]}")
            else:
                seen_ids[rule_id] = path

        if rule_name:
            if rule_name in seen_names:
                errors.append(f"Duplicate name: {rule_name} also used in {seen_names[rule_name]}")
            else:
                seen_names[rule_name] = path

        if errors:
            failed = True
            print("[FAIL]")
            for error in errors:
                print(f"  - {error}")
        else:
            print("[OK]")

        print()

    if failed:
        print("Some rules failed validation.")
        sys.exit(1)

    print("All Splunk rules are valid.")


if __name__ == "__main__":
    main()
