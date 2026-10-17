"""Render a GitLab card using the profile's existing Synthwave card design."""
from pathlib import Path
from copy import deepcopy
import math
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def render_card(root, merge_requests, events):
    svg = ET.parse(root / 'assets/gnome-stats-template.svg').getroot()
    q = lambda name: '{' + NS + '}' + name
    merged = sum(mr['state'] == 'merged' for mr in merge_requests)
    opened = sum(mr['state'] == 'opened' for mr in merge_requests)
    discussions = {(e['project_id'], e['note']['noteable_iid']) for e in events
                   if (e.get('note') or {}).get('noteable_type') == 'Issue'
                   and not e['note'].get('system')}
    projects = {e['project_id'] for e in events}
    values = [len(merge_requests), merged, opened, len(discussions), len(projects)]
    labels = ['Merge Requests:', 'Merged:', 'Open:', 'Issues Discussed (90d):', 'Projects (90d):']
    svg.find(q('title')).text = "Themazecrawler's GNOME GitLab Stats"
    svg.find(q('desc')).text = ', '.join(f'{label} {value}' for label, value in zip(labels, values))
    svg.set('aria-labelledby', 'titleId descId')
    style = svg.find(q('style'))
    style.text = """
      .header {font:600 18px 'Segoe UI',Ubuntu,Sans-Serif;fill:#e2e9ec}
      .stat {font:600 14px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:#e5289e}
      .icon {fill:#ef8539}
      .rank-text {font:600 24px 'Segoe UI',Ubuntu,Sans-Serif;fill:#e5289e}
      .rank-label {font:600 10px 'Segoe UI',Ubuntu,Sans-Serif;fill:#e2e9ec}
    """
    for node in svg.iter(q('text')):
        if node.get('data-testid') == 'header':
            node.text = "Themazecrawler's GitLab Stats"
    groups = [g for g in svg.iter(q('g')) if g.get('class') == 'stagger']
    mr_icon = deepcopy(groups[2].find(q('svg')))
    for group in groups[:3]:
        group.remove(group.find(q('svg')))
        group.insert(0,deepcopy(mr_icon))
    for group,label,value in zip(groups,labels,values):
        group.attrib.pop('style',None)
        texts = group.findall(q('text'))
        texts[0].text = label
        texts[1].text = str(value)
    ring = next(g for g in svg.iter(q('g')) if g.get('data-testid') == 'rank-circle')
    ring.clear()
    ring.set('transform','translate(380.5,110.5)')
    # Ring is a real merge ratio, never a fabricated developer rank.
    circumference = 2 * math.pi * 40
    fraction = merged / len(merge_requests) if merge_requests else 0
    for opacity,extra in [('0.2',{}),('0.8',{'stroke-dasharray':f'{circumference*fraction} {circumference}', 'transform':'rotate(-90)'})]:
        ET.SubElement(ring,q('circle'),{'r':'40','fill':'none','stroke':'#e2e9ec','stroke-width':'6','opacity':opacity,**extra})
    ET.SubElement(ring,q('text'),{'class':'rank-text','text-anchor':'middle','y':'3'}).text=f'{merged}/{len(merge_requests)}'
    ET.SubElement(ring,q('text'),{'class':'rank-label','text-anchor':'middle','y':'21'}).text='MERGED'
    # main-card-body already translates by 55 pixels.
    ring.set('transform','translate(380.5,55.5)')
    out = root / 'assets/gnome-stats.svg'
    out.parent.mkdir(exist_ok=True)
    ET.ElementTree(svg).write(out,encoding='unicode')
    return values
