# SIEM Rules as Code

This project manages SIEM detection rules from GitHub.

## Goal

The goal is to avoid writing and updating detection rules manually inside SIEM platforms.  
GitHub is used as the source of truth, and rules are deployed to SIEM platforms through APIs.

## Current Scope

- Splunk detection rules
- YAML-based detection format
- Rule validation
- Dry-run deployment
- API-based Splunk deployment
- GitHub Actions pipeline

QRadar integration will be added later.

## Project Structure

```text
rules/
  splunk/
    *.yml

scripts/
  validate_rules.py
  deploy_splunk.py

.github/workflows/
  splunk-rules.yml
