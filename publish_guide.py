#!/usr/bin/env python3
"""Publish a validated, quality-checked XMLTV feed without reporting stale matches.

No streaming URLs, usernames, passwords or provider-specific stream IDs are used.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
import argparse, csv, gzip, json, shutil


def validate_and_publish(source: Path, destination: Path, *, min_channels=1500,
                         min_programmes=160000, min_recent_sample=100) -> dict:
    if not source.is_file():
        raise RuntimeError('Candidate guide missing; existing published guide must remain unchanged')
    channels, programs, current = 0, 0, 0
    counts = Counter()
    channel_ids = set()
    now = datetime.now(timezone.utc)
    with gzip.open(source,'rb') as f:
        context=ET.iterparse(f,events=('start','end'))
        root=None
        for kind,el in context:
            if root is None and kind=='start':
                if el.tag!='tv':raise RuntimeError('Invalid XMLTV document: expected <tv>')
                root=el
            if kind!='end':continue
            if el.tag=='channel':
                cid=el.get('id')
                if cid in channel_ids:raise RuntimeError(f'Duplicate channel element {cid}')
                if cid:channel_ids.add(cid)
                channels+=1
            elif el.tag=='programme':
                cid=el.get('channel','')
                counts[cid]+=1
                programs+=1
                if programs%20==0:
                    try:
                        dt=datetime.strptime(el.attrib['start'][:20],'%Y%m%d%H%M%S %z')
                        if now-timedelta(hours=6)<=dt<=now+timedelta(days=16):current+=1
                    except (KeyError,ValueError):pass
            if el.tag in ('channel','programme'):
                el.clear()
                root.clear()
    if not set(counts).issubset(channel_ids):
        raise RuntimeError('Programme elements reference undeclared channel IDs')
    if channels<min_channels or programs<min_programmes or current<min_recent_sample:
        raise RuntimeError(f'Insufficient useful guide: channel_ids={channels}, programmes={programs}, near_future_sample={current}')
    # Don't touch the release until all checks succeeded.
    destination.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination/'guide.xml.gz')
    with gzip.open(source,'rb') as inp,(destination/'guide.xml').open('wb') as out:
        shutil.copyfileobj(inp,out,1024*1024)
    (destination/'.nojekyll').write_text('',encoding='utf-8')
    summary={'generated_utc':datetime.now(timezone.utc).isoformat(),
             'channel_ids':channels,'programmes':programs,
             'recent_future_sample_1_in_20':current,
             'important':'Published programmes are checked for overlapping contradictory titles. A matching tvg-id or manually assigned guide is still needed in TiviMate.'}
    source_report=source.parent/'EPG_Match_Report.csv'
    if source_report.is_file():
        coverage={}
        with source_report.open('r',encoding='utf-8-sig',newline='') as fh:
            for row in csv.DictReader(fh):
                region=row.get('Region','OTHER')
                stats=coverage.setdefault(region,{'total':0,'with_programmes':0,'without_programmes':0,
                              'with_playlist_epg_id':0,'potential_auto_id_with_programmes':0})
                stats['total']+=1
                epg_id=(row.get('EPGChannelID') or '').strip()
                actual=counts.get(row.get('FinalEPGID',''),0)>0
                stats['with_programmes' if actual else 'without_programmes']+=1
                if epg_id:stats['with_playlist_epg_id']+=1
                if actual and epg_id:stats['potential_auto_id_with_programmes']+=1
        summary['coverage_by_region']=coverage
        summary['actual_listed_channels']=sum(v['with_programmes'] for v in coverage.values())
        summary['target_channels']=sum(v['total'] for v in coverage.values())
        (destination/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    quality=source.parent/'EPG_Quality_Report.json'
    if quality.is_file():
        obj=json.loads(quality.read_text(encoding='utf-8'))
        summary['quality_check']={k:v for k,v in obj.items() if k not in ('unresolved_title_conflict_samples','window_utc')}
        (destination/'quality.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    (destination/'status.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (destination/'index.html').write_text('<!doctype html><html><meta charset="utf-8"><title>EPG quality checked</title><h1>EPG guide</h1><p><a href="guide.xml.gz">Guide XMLTV (gzip)</a></p><p><a href="status.json">Status</a> / <a href="quality.json">Quality audit</a></p></html>',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',default='generated/Quality_Checked_EPG.xml.gz')
    p.add_argument('--destination',default='site')
    opts=p.parse_args()
    validate_and_publish(Path(opts.candidate),Path(opts.destination))