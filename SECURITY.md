# Security & AI Privacy Policy

Because the Talent Intelligence Agent processes organizational metadata and utilizes Generative AI to evaluate human employees, security and privacy are our absolute highest priorities.

## Supported Versions

Currently, only the `main` branch of the Talent Intelligence Agent is supported with security updates. 

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

## Project-Specific Security Features & Vulnerabilities

When investigating or reporting vulnerabilities, we ask security researchers to pay special attention to our unique feature architecture. We are highly interested in vulnerabilities relating to:

1. **AI Prompt Injection (`src/actions/`)**: 
   - *Feature*: We send mathematical metrics to the Google Gemini API to draft manager emails.
   - *Vulnerability*: If you discover a way to trick the Gemini (`gemini-2.5-flash`) prompt into generating harmful, biased interventions or exposing raw underlying JSON metrics to the UI.

2. **DuckDB SQL Injection (`src/coral/`)**: 
   - *Feature*: The Coral Engine uses DuckDB `read_json_auto()` to mount user-generated `.jsonl` files.
   - *Vulnerability*: If you discover a way to inject malicious SQL through the Slack/GitHub API payloads that allows arbitrary code execution or filesystem traversal on the host machine.

3. **Data Evaporation Failures (Privacy Guarantee)**: 
   - *Feature*: The Coral engine is strictly designed to be purely in-memory. 
   - *Vulnerability*: If you discover that DuckDB or the Agent Pipeline is permanently persisting sensitive Slack metadata or GitHub commit data to the disk (beyond the temporary server boot phase), this is a critical privacy failure.

4. **API Key Leakage (`webapp/`)**: 
   - *Feature*: The FastAPI server holds credentials for multiple SaaS platforms.
   - *Vulnerability*: Any endpoint or traceback error that inadvertently exposes the GitHub `GITHUB_TOKEN`, `SLACK_BOT_TOKEN`, or Google Calendar OAuth tokens to the end-user dashboard.

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please do **NOT** create a public GitHub issue. 

Instead, please responsibly disclose it by sending an email to our security team:
**security@yourdomain.com**

Please include the following information in your email:
- A detailed description of the vulnerability.
- Step-by-step instructions to reproduce the issue (using `USE_MOCK_DATA="true"` if possible).
- The environment in which the issue was discovered.
- Which specific project feature (Gemini, Coral, FastAPI) is impacted.

### Triage Process
1. We will acknowledge receipt of your vulnerability report within 48 hours.
2. We will triage the vulnerability and aim to verify it within 5 business days.
3. Once verified, we will work on a patch and notify you of our progress.
4. After the patch is released, we will publicly acknowledge your contribution in our release notes.
