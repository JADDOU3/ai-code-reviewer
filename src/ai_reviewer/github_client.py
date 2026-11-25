import json

import requests

from .models import PullRequest

GITHUB_API = "https://api.github.com"


def load_pull_request(event_path: str, repo: str) -> PullRequest:
    """Read PR details from the event file that GitHub Actions provides."""
    with open(event_path, encoding="utf-8") as f:
        event = json.load(f)
    pr = event["pull_request"]
    return PullRequest(
        repo=repo,
        number=pr["number"],
        title=pr["title"],
        body=pr.get("body") or "",
    )


class GitHubClient:
    def __init__(self, token: str, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_pull_request(self, repo: str, number: int) -> PullRequest:
        """Fetch PR details from the API (used for local runs)."""
        response = self.session.get(
            f"{GITHUB_API}/repos/{repo}/pulls/{number}", timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        return PullRequest(
            repo=repo,
            number=data["number"],
            title=data["title"],
            body=data.get("body") or "",
        )

    def get_diff(self, repo: str, number: int) -> str:
        response = self.session.get(
            f"{GITHUB_API}/repos/{repo}/pulls/{number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def upsert_comment(self, repo: str, number: int, body: str, marker: str) -> None:
        """Update our previous review comment if it exists; otherwise create a new one."""
        url = f"{GITHUB_API}/repos/{repo}/issues/{number}/comments"
        response = self.session.get(url, params={"per_page": 100}, timeout=self.timeout)
        response.raise_for_status()

        for comment in response.json():
            if marker in comment["body"]:
                self.session.patch(
                    f"{GITHUB_API}/repos/{repo}/issues/comments/{comment['id']}",
                    json={"body": body},
                    timeout=self.timeout,
                ).raise_for_status()
                return

        self.session.post(url, json={"body": body}, timeout=self.timeout).raise_for_status()