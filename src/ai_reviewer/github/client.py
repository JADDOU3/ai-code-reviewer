import json

import requests

from ..models import PullRequest

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
        base_ref=pr["base"]["ref"],
        head_sha=pr["head"]["sha"],
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
            base_ref=data["base"]["ref"],
            head_sha=data["head"]["sha"],
        )

    def get_diff(self, repo: str, number: int) -> str:
        response = self.session.get(
            f"{GITHUB_API}/repos/{repo}/pulls/{number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        """Read a file's text from a branch. Returns None if the file doesn't exist."""
        response = self.session.get(
            f"{GITHUB_API}/repos/{repo}/contents/{path}",
            params={"ref": ref},
            headers={"Accept": "application/vnd.github.raw+json"},
            timeout=self.timeout,
        )
        if response.status_code == 404:
            return None
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

    def create_review(
        self, repo: str, number: int, commit_id: str, body: str, comments: list[dict]
    ) -> None:
        """Post a PR review with comments on specific lines."""
        if not comments:
            return
        self.session.post(
            f"{GITHUB_API}/repos/{repo}/pulls/{number}/reviews",
            json={
                "commit_id": commit_id,
                "event": "COMMENT",  # just comment; don't approve or request changes
                "body": body,
                "comments": comments,
            },
            timeout=self.timeout,
        ).raise_for_status()