#!/usr/bin/env python3
"""Read-only audit of the exact sanitized XMLTV that TiviMate downloads."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import gzip, json, re, sys
import xml.etree.ElementTree as ET


def audit_guide(path):
    now=datetime.now(timezone.utc)
    known={}
    counts=Counter()
    upcoming={}
    with gzip.open(path,'rb') if str(path).endswith('.gz') else open(path,'rb') as file:
        context=ET.iterparse(file,events=('start','end'))
        root=None
        for event,elem in context:
            if root is None and event=='start':
                root=elem
            if event!='end':
                continue
            if elem.tag=='channel':
                cid=elem.get('id','')
                names=[(n.text or '').strip() for n in elem.findall('display-name')]
                if re.search(r'tv[ ._-]*land',cid,re.I) or any(re.search(r'tv[ ._-]*land',n,re.I) for n in names):
                    known[cid]=names
                    upcoming[cid]=[]
                elem.clear()
                if root is not None:root.clear()
            elif elem.tag=='programme':
                cid=elem.get('channel','')
                if cid in known:
                    counts[cid]+=1
                    start=elem.get('start','')
                    title=elem.findtext('title','')
                    try:
                        # XMLTV timestamps include UTC offset (e.g. +0000).
                        dt=datetime.strptime(start[:20],'%Y%m%d%H%M%S %z').astimezone(timezone.utc)
                        if now <= dt <= now.replace(year=now.year+1) and len(upcoming[cid])<4:
                            upcoming[cid].append({'start':start,'title':title})
                    except (ValueError,IndexError):
                        pass
                elem.clear()
                if root is not None:root.clear()
    results=[{'id':k,'names':v,'programmes':counts[k],'upcoming_sample':upcoming[k]} for k,v in known.items()]
    return {'channel_blocks':len(results),'with_programmes':sum(x['programmes']>0 for x in results),
            'entries':results,'note':'EPG options may be filtered/cached by TiviMate; mere source IDs do not ensure visible choices.'}


def main():
    if len(sys.argv)<2:
        raise SystemExit('Usage: python audit_tvland.py guide.xml.gz')
    report=audit_guide(sys.argv[1])
    print('TVLAND_AUDIT_JSON_START')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    print('TVLAND_AUDIT_JSON_END')
    Path('generated').mkdir(exist_ok=True)
    Path('generated/TVLAND_Actual_File_Audit.json').write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    main()
