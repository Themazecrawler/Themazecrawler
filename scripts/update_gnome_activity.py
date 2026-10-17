"""Refresh the public GNOME GitLab section of the profile README.

Only public activity is requested. No GitLab token or third-party stats host
is needed. Push commit counts are deliberately not summed: branch creation,
rebases, and force pushes can include upstream or repeated commits.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

BASE = "https://gitlab.gnome.org"
USERNAME = "themazecrawler"
ROOT = Path(__file__).resolve().parents[1]
START = "<!-- GNOME-ACTIVITY:START -->"
END = "<!-- GNOME-ACTIVITY:END -->"


def get(path, **params):
    url = BASE + "/api/v4" + path
    if params:
        url += "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": "GNOME-profile-activity/1.0", "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=40) as response:
                return json.load(response), response.headers.get("X-Next-Page", "")
        except (HTTPError, URLError, TimeoutError) as error:
            retryable = not isinstance(error, HTTPError) or error.code == 429 or error.code >= 500
            if not retryable or attempt == 2:
                raise
            time.sleep(2 ** attempt)


def pages(path, **params):
    result = []
    page = "1"
    seen = set()
    while page:
        if page in seen or len(seen) >= 200:
            raise RuntimeError("Pagination did not finish; keeping the previous README")
        seen.add(page)
        items, page = get(path, **params, per_page=100, page=page)
        if not isinstance(items, list):
            raise RuntimeError("Expected a GitLab list response")
        result.extend(items)
    return result


def text(value):
    # Keep remote titles from introducing Markdown/HTML into the profile.
    value = re.sub(r"\s+", " ", str(value)).strip()
    for char in "\\`*_{}[]<>()|":
        value = value.replace(char, "&#%d;" % ord(char))
    return value


def link(label, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "gitlab.gnome.org":
        raise ValueError("Unexpected activity link host")
    return f"[{text(label)}]({url})"


def render(user, merge_requests, issues, events, projects, now):
    events = sorted(events, key=lambda event: event["created_at"], reverse=True)
    discussions = {}
    commits = {}
    for event in events:
        project_id = event["project_id"]
        note = event.get("note") or {}
        if note.get("noteable_type") == "Issue" and not note.get("system"):
            iid = note["noteable_iid"]
            key = (project_id, iid)
            discussions.setdefault(key, event)
        push = event.get("push_data") or {}
        sha = push.get("commit_to")
        if sha and push.get("ref_type") == "branch" and push.get("action") != "removed":
            commits.setdefault((project_id, push.get("ref") or sha), event)

    merged = sum(mr["state"] == "merged" for mr in merge_requests)
    opened = sum(mr["state"] == "opened" for mr in merge_requests)
    lines = [
        "### GNOME / GitLab Contributions",
        "",
        link("@themazecrawler on GNOME GitLab", user["web_url"]),
        "",
        "| Merge requests | Merged | Open | Issues opened | Issues discussed (last 90 days) |",
        "| :---: | :---: | :---: | :---: | :---: |",
        f"| {len(merge_requests)} | {merged} | {opened} | {len(issues)} | {len(discussions)} |",
        "",
        "**Recent merge requests**",
        "",
    ]
    for mr in sorted(merge_requests, key=lambda item: item["created_at"], reverse=True)[:5]:
        ref = mr.get("references", {}).get("full", "!" + str(mr["iid"]))
        status = "Draft" if mr.get("draft") else mr["state"].capitalize()
        lines.append(f"- **{status}** - {link(ref + ': ' + mr['title'], mr['web_url'])}")
    if not merge_requests:
        lines.append("No public merge requests yet.")
    lines += ["", "**Latest pushed commit per branch (last 90 days)**", ""]
    for (pid, _), event in list(commits.items())[:5]:
        sha = event["push_data"]["commit_to"]
        project = projects[pid]
        title = event["push_data"].get("commit_title") or sha[:8]
        url = project["web_url"] + "/-/commit/" + sha
        label = project["path_with_namespace"] + " " + sha[:8] + ": " + title
        lines.append("- " + link(label, url))
    if not commits:
        lines.append("No public branch push activity in this period.")
    lines += ["", "**Recent issue discussions (last 90 days)**", ""]
    for (pid, iid), event in list(discussions.items())[:5]:
        project = projects[pid]
        url = project["web_url"] + f"/-/issues/{iid}"
        label = project["path_with_namespace"] + f"#{iid}: " + event.get("target_title", "Issue discussion")
        lines.append("- " + link(label, url))
    if not discussions:
        lines.append("No public issue discussions in this period.")
    lines += [
        "",
        f"<sub>Updated {now:%Y-%m-%d} UTC from public GNOME GitLab activity. "
        "MR and issue totals cover publicly visible authored items; commits show the latest "
        "branch tips from push events rather than a lifetime commit count. "
        "GitLab activity is displayed separately from GitHub's contribution graph.</sub>",
    ]
    return "\n".join(lines)


def main():
    now = datetime.now(timezone.utc)
    users, _ = get("/users", username=USERNAME)
    matches = [user for user in users if user["username"] == USERNAME]
    if len(matches) != 1:
        raise RuntimeError("Could not resolve one exact GNOME GitLab user")
    user = matches[0]
    uid = user["id"]
    merge_requests = pages("/merge_requests", scope="all", state="all", author_id=uid)
    issues = pages("/issues", scope="all", state="all", author_id=uid)
    events = pages(f"/users/{uid}/events", after=(now - timedelta(days=90)).strftime("%Y-%m-%d"))
    project_ids = {event["project_id"] for event in events}
    projects = {pid: get(f"/projects/{pid}")[0] for pid in sorted(project_ids)}
    section = render(user, merge_requests, issues, events, projects, now)
    readme = ROOT / "README.md"
    original = readme.read_text()
    if original.count(START) != 1 or original.count(END) != 1:
        raise RuntimeError("Expected exactly one GNOME activity marker pair")
    before, remainder = original.split(START, 1)
    _, after = remainder.split(END, 1)
    updated = before + START + "\n" + section + "\n" + END + after
    if updated != original:
        readme.write_text(updated)
    print(f"GNOME profile refreshed: {len(merge_requests)} merge requests, {len(issues)} authored issues.")


if __name__ == "__main__":
    main()
