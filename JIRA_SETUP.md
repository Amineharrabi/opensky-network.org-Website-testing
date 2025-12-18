# Jira integration (optional)

The test runner can auto-create a Jira issue when a test fails and attach artifacts (screenshot/HTML/console logs).

## Required environment variables
- `JIRA_BASE_URL` (example: `https://your-company.atlassian.net`)
- `JIRA_EMAIL` (your Atlassian account email)
- `JIRA_API_TOKEN` (API token generated in Atlassian)

## Usage
- Run tests with Jira creation enabled:
  - `pytest -m audit --jira-create-on-fail --jira-project=QA --jira-label=opensky`

## Notes
- This uses Jira REST API v3 endpoints (`/rest/api/3/...`), intended for Jira Cloud.
- Keep `--jira-create-on-fail` off by default to avoid creating issues unintentionally.

