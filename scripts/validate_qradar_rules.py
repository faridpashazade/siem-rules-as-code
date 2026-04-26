import sys
from pathlib import Path

import yaml


RULES_DIR = Path("rules/qradar")

REQUIRED_TOP_LEVEL_FIELDS = [
    "id",
    "name",
    "description",
    "enabled",
    "severity",
    "qradar",
]

REQUIRED_QRADAR_FIELDS = [
    "rule_type",
    "offense",
    "offense_index",
    "rule_group",
    "log_source_type",
    "qradar_rule_logic",
    "rule_response",
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

    qradar = rule.get("qradar")
    if not isinstance(qradar, dict):
        errors.append("qradar field must be an object.")
        return errors

    for field in REQUIRED_QRADAR_FIELDS:
        if field not in qradar:
            errors.append(f"Missing qradar field: {field}")

    if qradar.get("offense") is not True:
        errors.append("qradar.offense must be true for this project.")

    logic = qradar.get("qradar_rule_logic", "")
    if not isinstance(logic, str) or not logic.strip():
        errors.append("qradar.qradar_rule_logic is empty.")

    response = qradar.get("rule_response", "")
    if not isinstance(response, str) or "offense" not in response.lower():
        errors.append("qradar.rule_response must mention offense creation.")

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

    print(f"Found {len(rule_files)} QRadar rule files.\n")

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
        print("Some QRadar rules failed validation.")
        sys.exit(1)

    print("All QRadar rules are valid.")


if __name__ == "__main__":
    main()
