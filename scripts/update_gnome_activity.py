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
    from render_gnome_card import render_card
    render_card(ROOT, merge_requests, events)
    return '[![GNOME GitLab Stats](./assets/gnome-stats.svg)](https://gitlab.gnome.org/themazecrawler)' + '\n'


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
    projects = {}
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
