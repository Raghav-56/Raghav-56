#!/usr/bin/env python3
"""Summarize recent public GitHub activity in the profile README."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

USER = "Raghav-56"
START = "<!--START_SECTION:activity-->"
END = "<!--END_SECTION:activity-->"
API = "https://api.github.com"


def get_json(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-activity"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(API + path, headers=headers), timeout=30) as response:
        return json.load(response)


def plain(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:117] + "..." if len(text) > 120 else text
    return re.sub(r"([\\`*\[\]<>_])", r"\\\1", text)


def select(events):
    """Find supported events in their original, newest-first order."""
    selected = []
    for event in events:
        repo = event["repo"]["name"]
        if repo.lower() == f"{USER}/{USER}".lower():
            continue
        payload = event["payload"]
        kind = event["type"]
        if kind == "PushEvent" and payload.get("head"):
            selected.append((event, "commit", payload["head"]))
        elif kind == "PullRequestEvent" and payload.get("action") in ("opened", "merged") and payload.get("number"):
            selected.append((event, "pull", payload["number"]))
        elif kind == "IssuesEvent" and payload.get("action") in ("opened", "closed", "reopened") and payload.get("issue", {}).get("number"):
            selected.append((event, "issue", payload["issue"]["number"]))
        elif kind == "ReleaseEvent" and payload.get("action") == "published" and payload.get("release", {}).get("html_url"):
            selected.append((event, "release", None))
        else:
            continue
    return selected


def render(events, fetch=get_json):
    rows = []
    seen = set()
    for event, kind, identifier in select(events):
        repo = event["repo"]["name"]
        if repo.lower() in seen:
            continue
        repo_path = "/".join(quote(part, safe="") for part in repo.split("/"))
        repo_url = f"https://github.com/{repo_path}"
        payload = event["payload"]
        if kind == "commit":
            item = fetch(f"/repos/{repo_path}/commits/{quote(identifier, safe='')}")
            title = item["commit"]["message"].splitlines()[0]
            if re.match(r"merge (?:pull request|upstream|branch)\b", title, re.IGNORECASE):
                continue
            url = f"{repo_url}/commit/{quote(identifier, safe='')}"
            verb = "Pushed"
        elif kind == "pull":
            item = fetch(f"/repos/{repo_path}/pulls/{identifier}")
            title, url = item["title"], f"{repo_url}/pull/{identifier}"
            verb = "Merged" if payload["action"] == "merged" else "Opened PR"
        elif kind == "issue":
            item = fetch(f"/repos/{repo_path}/issues/{identifier}")
            title, url = item["title"], f"{repo_url}/issues/{identifier}"
            verb = payload["action"].capitalize() + " issue"
        else:
            item = payload["release"]
            title = item.get("name") or item["tag_name"]
            url = item["html_url"]
            verb = "Released"
        date = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")).strftime("%b %d, %Y").replace(" 0", " ")
        rows.append(f"- **[{plain(repo)}]({repo_url})** · {verb} [{plain(title)}]({url}) · {date}")
        seen.add(repo.lower())
        if len(rows) == 5:
            break
    if not rows:
        rows.append("No recent public GitHub activity to show.")
    return "\n".join(rows)


def main():
    events = []
    for page in range(1, 4):
        batch = get_json(f"/users/{USER}/events/public?per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Unexpected events response")
        events.extend(batch)
        if len(batch) < 100:
            break
    content = render(events)
    path = Path("README.md")
    readme = path.read_text(encoding="utf-8")
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) >= readme.index(END):
        raise ValueError("Activity markers are missing or out of order")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    path.write_text(f"{before}{START}\n{content}\n{END}{after}", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Activity update failed: {exc}", file=sys.stderr)
        sys.exit(1)
