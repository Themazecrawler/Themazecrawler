"""Generate the profile's Synthwave stats card and green contribution grid."""
from datetime import timedelta
from copy import deepcopy
import xml.etree.ElementTree as ET

NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
q=lambda name:'{'+NS+'}'+name


def render_card(root,metrics):
    svg=ET.parse(root/'assets/gnome-stats-template.svg').getroot()
    labels=['Total Merge Requests:','Total Issues:','Total Projects:','Total Commits:']
    values=[metrics[key] for key in ['mrs','issues','projects','commits']]
    svg.find(q('title')).text="Themazecrawler's GitLab Stats"
    svg.find(q('desc')).text=', '.join(f'{label} {value}' for label,value in zip(labels,values))+'. Public authored issues, contributed projects, and unique authored commit SHAs across public repositories.'
    svg.set('aria-labelledby','titleId descId')
    svg.find(q('style')).text="""
      .header {font:600 18px 'Segoe UI',Ubuntu,Sans-Serif;fill:#e2e9ec}
      .stat {font:600 14px 'Segoe UI',Ubuntu,'Helvetica Neue',Sans-Serif;fill:#e5289e}
      .icon {fill:#ef8539}
    """
    for node in svg.iter(q('text')):
        if node.get('data-testid')=='header':node.text="Themazecrawler's GitLab Stats"
    body=next(g for g in svg.iter(q('g')) if g.get('data-testid')=='main-card-body')
    ring=next(g for g in body if g.get('data-testid')=='rank-circle')
    body.remove(ring)
    groups=[g for g in svg.iter(q('g')) if g.get('class')=='stagger']
    icons=[deepcopy(groups[i].find(q('svg'))) for i in [2,3,4,1]]
    for group,label,value,icon in zip(groups,labels,values,icons):
        group.attrib.pop('style',None)
        group.remove(group.find(q('svg')));group.insert(0,icon)
        texts=group.findall(q('text'));texts[0].text=label;texts[1].text=str(value)
        texts[1].set('x','365')
        texts[1].set('text-anchor','end')
    # Remove the old fifth metric and center four rows in the original card.
    container=next(g for g in body if g.tag==q('svg'))
    container.remove(list(container)[4])
    container.set('y','8')
    ET.ElementTree(svg).write(root/'assets/gnome-stats.svg',encoding='unicode')


def render_calendar(root,counts,today):
    since=today-timedelta(days=364)
    start=since-timedelta(days=(since.weekday()+1)%7)
    weeks=(today-start).days//7+1
    step=14;cell=11;left=44;top=64;width=left+weeks*step+24
    svg=ET.Element(q('svg'),{'xmlns':NS,'width':str(width),'height':'210','viewBox':f'0 0 {width} 210','role':'img','aria-labelledby':'calendar-title calendar-desc'})
    # Namespace registration handles xmlns during serialization.
    svg.attrib.pop('xmlns')
    ET.SubElement(svg,q('title'),{'id':'calendar-title'}).text='GitLab Contribution Calendar'
    total=sum(value for day,value in counts.items() if since.isoformat()<=day<=today.isoformat())
    ET.SubElement(svg,q('desc'),{'id':'calendar-desc'}).text=f'{total} public contributions in the last 365 days, from the native GNOME GitLab calendar.'
    ET.SubElement(svg,q('rect'),{'x':'.5','y':'.5','width':str(width-1),'height':'209','rx':'4.5','fill':'#2b213a','stroke':'#e4e2e2'})
    style=ET.SubElement(svg,q('style'));style.text="text{font-family:'Segoe UI',Ubuntu,Sans-Serif;fill:#e2e9ec}.title{font-size:18px;font-weight:600}.label{font-size:10px}.caption{font-size:11px;fill:#b7a7c6}"
    ET.SubElement(svg,q('text'),{'x':'25','y':'30','class':'title'}).text='GitLab Contribution Calendar'
    ET.SubElement(svg,q('text'),{'x':str(width-25),'y':'29','class':'caption','text-anchor':'end'}).text=f'{total} contributions in the last year'
    colors=['#382c49','#0e4429','#006d32','#26a641','#39d353']
    maximum=max([v for day,v in counts.items() if since.isoformat()<=day<=today.isoformat()]+[1])
    previous_month=None
    for week in range(weeks):
        first=start+timedelta(days=week*7)
        if first.month!=previous_month and week<weeks-1:
            ET.SubElement(svg,q('text'),{'x':str(left+week*step),'y':'54','class':'label'}).text=first.strftime('%b')
            previous_month=first.month
        for row in range(7):
            day=first+timedelta(days=row)
            if day<since or day>today:continue
            n=counts.get(day.isoformat(),0)
            level=0 if n==0 else min(4,1+(n*3)//maximum)
            rect=ET.SubElement(svg,q('rect'),{'x':str(left+week*step),'y':str(top+row*step),'width':str(cell),'height':str(cell),'rx':'2','fill':colors[level]})
            ET.SubElement(rect,q('title')).text=f'{day.isoformat()}: {n} contributions'
    for row,label in [(1,'Mon'),(3,'Wed'),(5,'Fri')]:
        ET.SubElement(svg,q('text'),{'x':'12','y':str(top+row*step+9),'class':'label'}).text=label
    ET.SubElement(svg,q('text'),{'x':'25','y':'191','class':'caption'}).text='GNOME GitLab · Public activity'
    ET.SubElement(svg,q('text'),{'x':str(width-155),'y':'191','class':'label'}).text='Less'
    for i,color in enumerate(colors):
        ET.SubElement(svg,q('rect'),{'x':str(width-125+i*14),'y':'182','width':'11','height':'11','rx':'2','fill':color})
    ET.SubElement(svg,q('text'),{'x':str(width-25),'y':'191','class':'label','text-anchor':'end'}).text='More'
    ET.ElementTree(svg).write(root/'assets/gnome-calendar.svg',encoding='unicode')
