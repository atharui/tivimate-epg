#!/usr/bin/env python3
"""Read-only check: printed EPG listings at a documented user observation time."""
import gzip,sys,json,datetime,xml.etree.ElementTree as ET
from pathlib import Path

TARGET={'comedycentral.us','comedycentral.uk'}
USER_OBSERVATION=datetime.datetime(2026,11,12,19,27,tzinfo=datetime.timezone.utc)

def audit(path):
    counts={k:0 for k in TARGET}
    at_time={k:[] for k in TARGET}
    rows={k:[] for k in TARGET}
    with gzip.open(path,'rb') if str(path).endswith('.gz') else open(path,'rb') as fh:
        context=ET.iterparse(fh,events=('start','end'))
        root=None
        for event,elem in context:
            if root is None and event=='start':root=elem
            if event!='end':continue
            if elem.tag=='programme':
                id_=elem.get('channel','')
                if id_ in TARGET:
                    counts[id_]+=1
                    try:
                        start=datetime.datetime.strptime(elem.get('start','')[:20],'%Y%m%d%H%M%S %z')
                        stop=datetime.datetime.strptime(elem.get('stop','')[:20],'%Y%m%d%H%M%S %z')
                    except ValueError:
                        start=stop=None
                    if start is not None and start <= USER_OBSERVATION < stop:
                        at_time[id_].append({'start':elem.get('start'), 'stop':elem.get('stop'), 'title':elem.findtext('title')})
                    if start is not None and abs((start-USER_OBSERVATION).total_seconds())<3600 and len(rows[id_])<6:
                        rows[id_].append({'start':elem.get('start'),'title':elem.findtext('title')})
                elem.clear()
                if root is not None:root.clear()
            elif elem.tag=='channel':
                elem.clear()
                if root is not None:root.clear()
    return {'time_utc':'2026-11-12T19:27:00Z',
            'time_riyadh':'2026-11-12T22:27:00+03:00',
            'guide_id_programme_counts':counts,'programmes_at_observation':at_time,
            'nearby_titles':rows,
            'note':'Live-stream identity based on user report; this does not guarantee future provider feeds stay unchanged.'}

if __name__=='__main__':
    result=audit(sys.argv[1])
    print('COMEDY_CENTRAL_EPG_AUDIT',json.dumps(result,ensure_ascii=False))
    Path('generated').mkdir(exist_ok=True)
    Path('generated/Comedy_Central_Audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
