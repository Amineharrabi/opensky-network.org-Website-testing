from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import requests


@dataclass(frozen=True)
class JiraIssueCreateRequest:
    project_key: str | None
    issue_type: str
    summary: str
    description: str
    labels: list[str]


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self._auth = (email, api_token)

    @staticmethod
    def from_env() -> "JiraClient":
        base_url = os.getenv("JIRA_BASE_URL")
        email = os.getenv("JIRA_EMAIL")
        api_token = os.getenv("JIRA_API_TOKEN")
        if not base_url or not email or not api_token:
            raise RuntimeError(
                "Missing Jira env vars. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN."
            )
        return JiraClient(base_url=base_url, email=email, api_token=api_token)

    def create_issue(self, req: JiraIssueCreateRequest) -> str:
        if not req.project_key:
            raise ValueError("Jira project key missing (use --jira-project).")

        url = f"{self.base_url}/rest/api/3/issue"
        description_adf = _text_to_adf(req.description)
        payload = {
            "fields": {
                "project": {"key": req.project_key},
                "issuetype": {"name": req.issue_type},
                "summary": req.summary,
                "description": description_adf,
                "labels": req.labels or [],
            }
        }
        resp = requests.post(url, json=payload, auth=self._auth, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["key"]

    def add_attachment(self, issue_key: str, file_path: Path) -> None:
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"
        headers = {"X-Atlassian-Token": "no-check"}
        with file_path.open("rb") as f:
            files = {"file": (file_path.name, f)}
            resp = requests.post(url, headers=headers, files=files, auth=self._auth, timeout=60)
            resp.raise_for_status()


def _text_to_adf(text: str) -> dict:
    """Convert a simple Markdown-ish string into Jira ADF.

    Supports:
    - blank lines -> paragraph breaks
    - "- item" lines -> bullet list
    """
    paragraphs: list[dict] = []
    bullet_items: list[dict] = []

    def flush_bullets() -> None:
        nonlocal bullet_items
        if bullet_items:
            paragraphs.append({"type": "bulletList", "content": bullet_items})
            bullet_items = []

    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_bullets()
            continue

        if line.lstrip().startswith("- "):
            item_text = line.lstrip()[2:].strip()
            bullet_items.append(
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": item_text}],
                        }
                    ],
                }
            )
            continue

        flush_bullets()
        paragraphs.append({"type": "paragraph", "content": [{"type": "text", "text": line}]})

    flush_bullets()

    return {"type": "doc", "version": 1, "content": paragraphs or [{"type": "paragraph"}]}
