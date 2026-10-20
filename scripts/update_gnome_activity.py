"""Refresh public GNOME GitLab totals and the native contribution calendar.

Commits are distinct authored SHAs across public contributed/owned repositories
and MR source repositories. Shared fork/upstream SHAs are counted once. Commit
revisions with different SHAs remain distinct, as in Git's object model.
Projects use GNOME's contributed-projects list plus authored MR targets and
previously observed contributed projects, rather than counting personal forks.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://gitlab.gnome.org'
USERNAME = 'themazecrawler'
ROOT = Path(__file__).resolve().parents[1]
START = '<!-- GNOME-ACTIVITY:START -->'
END = '<!-- GNOME-ACTIVITY:END -->'


def get_url(url):
    request = Request(url, headers={'User-Agent':'GNOME-profile-activity/1.0','Accept':'application/json'})
    # gitlab.gnome.org occasionally returns 5xx responses for repository
    # commit queries for a minute or more. Scheduled jobs must outlive that
    # brief outage rather than abandoning the entire daily refresh.
    for attempt in range(6):
        try:
            with urlopen(request,timeout=40) as response:
                return json.load(response), response.headers.get('X-Next-Page','')
        except (HTTPError,URLError,TimeoutError) as error:
            if (isinstance(error,HTTPError) and error.code != 429 and error.code < 500) or attempt == 5:
                raise
            delay=min(30,3 * (2 ** attempt)) + random.random()
            print(f'GitLab request failed ({error}); retrying in {delay:.1f}s: {url}',flush=True)
            time.sleep(delay)


def get(path,**params):
    return get_url(BASE+'/api/v4'+path+('?' + urlencode(params) if params else ''))


def pages(path,**params):
    result=[]
    page='1'
    seen=set()
    while page:
        if page in seen or len(seen)>=200:
            raise RuntimeError('Pagination did not finish; retaining previous stats')
        seen.add(page)
        items,next_page=get(path,**params,per_page=100,page=page)
        if not isinstance(items,list):
            raise RuntimeError('Expected a GitLab list response')
        result.extend(items)
        page=next_page or (str(int(page)+1) if len(items)==100 else '')
    return result


def main():
    now=datetime.now(timezone.utc)
    users,_=get('/users',username=USERNAME)
    matches=[u for u in users if u['username']==USERNAME]
    if len(matches)!=1:
        raise RuntimeError('Expected one exact GNOME GitLab account')
    user=matches[0]
    uid=user['id']
    with ThreadPoolExecutor(max_workers=5) as pool:
        mr_job=pool.submit(pages,'/merge_requests',scope='all',state='all',author_id=uid)
        issue_job=pool.submit(pages,'/issues',scope='all',state='all',author_id=uid)
        project_job=pool.submit(pages,f'/users/{uid}/contributed_projects')
        owned_job=pool.submit(pages,f'/users/{uid}/projects')
        calendar_job=pool.submit(get_url,BASE+f'/users/{USERNAME}/calendar.json')
        mrs=mr_job.result();issues=issue_job.result();projects=project_job.result()
        owned=owned_job.result();calendar=calendar_job.result()[0]
    if not isinstance(calendar,dict) or any(not isinstance(v,int) or v<0 for v in calendar.values()):
        raise RuntimeError('Invalid native contribution calendar')
    old_path=ROOT/'assets/gnome-activity.json'
    old=json.loads(old_path.read_text()) if old_path.exists() else {}
    contributed_ids={p['id'] for p in projects}|{m['target_project_id'] for m in mrs}|set(old.get('contributed_project_ids',[]))
    repo_ids=contributed_ids|{p['id'] for p in owned}|{m['source_project_id'] for m in mrs if m.get('source_project_id')}
    authors={USERNAME,user['name']}
    names={name.casefold() for name in authors}
    def commits_for(job):
        pid,author=job
        return pages(f'/projects/{pid}/repository/commits',author=author,all='true')
    jobs=[(pid,author) for pid in sorted(repo_ids) for author in sorted(authors)]
    commit_ids=set()
    # Keep pressure on the public GNOME GitLab API low. Higher concurrency
    # caused repeatable HTTP 500s in scheduled GitHub Actions runs.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for commits in pool.map(commits_for,jobs):
            commit_ids.update(c['id'] for c in commits if c['author_name'].casefold() in names)
    # Fetch everything before touching generated files, so API failure retains
    # the previous successful public snapshot.
    metrics={'mrs':len(mrs),'issues':len(issues),'projects':len(contributed_ids),'commits':len(commit_ids)}
    readme=ROOT/'README.md';original=readme.read_text()
    if original.count(START)!=1 or original.count(END)!=1:
        raise RuntimeError('Expected exactly one activity marker pair')
    section='[![GNOME GitLab Stats](./assets/gnome-stats.svg)](https://gitlab.gnome.org/themazecrawler)\n\n[![GitLab Contribution Calendar](./assets/gnome-calendar.svg)](https://gitlab.gnome.org/themazecrawler)'
    before,remainder=original.split(START,1);_,after=remainder.split(END,1)
    updated=before+START+'\n'+section+'\n'+END+after
    from render_gnome_card import render_card,render_calendar
    render_card(ROOT,metrics)
    render_calendar(ROOT,calendar,now.date())
    old_path.write_text(json.dumps({'username':USERNAME,'updated':now.strftime('%Y-%m-%d'),'metrics':metrics,'contributed_project_ids':sorted(contributed_ids),'calendar':calendar},indent=2)+'\n')
    if updated!=original:
        readme.write_text(updated)
    print(json.dumps(metrics))


if __name__=='__main__':
    main()
