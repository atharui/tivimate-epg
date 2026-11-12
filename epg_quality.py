#!/usr/bin/env python3
"""Fail-safe XMLTV programme audit for TiviMate.

This does not invent listings, shift channel times or match broadcasters by guesswork.
Conflicting programme slots are quarantined rather than picking a random title.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import gzip
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

DATE_RE = re.compile(r'^(\d{14}|\d{12})\s+([+-]\d{4})$')


def timestamp(value: str | None) -> float | None:
    if not value:
        return None
    m = DATE_RE.fullmatch(value.strip())
    if not m:
        return None
    digits, offset = m.groups()
    try:
        fmt = '%Y%m%d%H%M%S %z' if len(digits) == 14 else '%Y%m%d%H%M %z'
        return datetime.strptime(digits + ' ' + offset, fmt).timestamp()
    except (ValueError, OverflowError):
        return None


def tidy_title(value):
    return re.sub(r'\s+', ' ', (value or '').strip()).casefold()


def audit_and_clean(source: Path, destination: Path, report_file: Path, *,
                    now: datetime | None = None, past_days: int = 7,
                    future_days: int = 16, max_loss: float = .18):
    now = now or datetime.now(timezone.utc)
    current_ts = now.timestamp()
    low = current_ts - past_days * 86400
    high = current_ts + future_days * 86400
    channels = {}
    events = defaultdict(list)
    counts = Counter()
    samples = []

    with gzip.open(source, 'rb') as fh:
        context = ET.iterparse(fh, events=('start', 'end'))
        root = None
        for kind, elem in context:
            if kind == 'start':
                if root is None:
                    if elem.tag != 'tv':
                        raise ValueError('EPG root is not <tv>')
                    root = elem
                continue
            if elem.tag == 'channel':
                cid = elem.get('id')
                if cid:
                    channels[cid] = ET.tostring(elem, encoding='utf-8')
                elem.clear()
                root.clear()
            elif elem.tag == 'programme':
                counts['input_programmes'] += 1
                cid = elem.get('channel', '')
                a, b = timestamp(elem.get('start')), timestamp(elem.get('stop'))
                title = tidy_title(elem.findtext('title'))
                if cid not in channels:
                    counts['missing_channel'] += 1
                elif not title:
                    counts['missing_title'] += 1
                elif a is None or b is None:
                    counts['invalid_time_format'] += 1
                elif not a < b or (b - a) > 24 * 3600:
                    counts['invalid_duration'] += 1
                elif b < low or a > high:
                    counts['outside_useful_window'] += 1
                else:
                    # Keep complete XMLTV children, including descriptions and languages.
                    events[cid].append((a, b, title, ET.tostring(elem, encoding='utf-8')))
                elem.clear()
                root.clear()

    retained = {}
    for cid, records in events.items():
        records.sort(key=lambda r: (r[0], r[1], r[2]))
        distinct = []
        seen = set()
        for rec in records:
            ident = (rec[0], rec[1], rec[2])
            if ident in seen:
                counts['duplicate_programmes'] += 1
                continue
            seen.add(ident)
            distinct.append(rec)
        # There may be multiple incompatible schedules from one EPG source.
        # Do not guess which title is correct when their times overlap.
        conflicted = set()
        active = []
        for i, rec in enumerate(distinct):
            a, b, title, _ = rec
            active = [j for j in active if distinct[j][1] > a + 120]
            for j in active:
                x = distinct[j]
                if x[2] != title and min(b, x[1]) - max(a, x[0]) > 120:
                    conflicted.add(i)
                    conflicted.add(j)
                    if len(samples) < 30:
                        samples.append({'epg_id':cid, 'titles':[x[2],title],
                                        'start_utc': datetime.fromtimestamp(a,timezone.utc).isoformat()})
            active.append(i)
        counts['contradictory_programme_records'] += len(conflicted)
        remaining = [r for i, r in enumerate(distinct) if i not in conflicted]
        if remaining:
            retained[cid] = remaining
        elif distinct:
            counts['channels_fully_quarantined'] += 1

    written = sum(map(len, retained.values()))
    valid_before_conflicts = sum(map(len, events.values()))
    if not valid_before_conflicts or not written:
        raise ValueError('No useful programmes after validation: keeping last published release')
    # Prevent partial upstream outages or parsing bugs from replacing a working guide.
    if written / counts['input_programmes'] < (1-max_loss):
        raise ValueError('Quality guard removed too many events; keeping last published release. '+
                         f'raw={counts["input_programmes"]} output={written}')
    destination.parent.mkdir(parents=True,exist_ok=True)
    tmp = destination.with_name(destination.name + '.tmp')
    try:
        with gzip.open(tmp,'wb',compresslevel=6) as out:
            out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            out.write(b'<tv generator-info-name="TiviMate EPG checked; ambiguous records excluded">\n')
            for cid in sorted(retained):
                out.write(channels[cid]+b'\n')
            for cid in sorted(retained):
                for row in retained[cid]:
                    out.write(row[3]+b'\n')
            out.write(b'</tv>\n')
        tmp.replace(destination)
    finally:
        if tmp.exists(): tmp.unlink()

    summary = dict(counts)
    summary.update({'output_programmes':written, 'output_channel_ids':len(retained),
                    'unresolved_title_conflict_samples':samples,
                    'quarantined_programmes_not_guessed':counts['contradictory_programme_records'],
                    'window_utc':{'from':datetime.fromtimestamp(low,timezone.utc).isoformat(),
                                  'until':datetime.fromtimestamp(high,timezone.utc).isoformat()}})
    report_file.parent.mkdir(parents=True,exist_ok=True)
    report_file.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('unresolved_title_conflict_samples','window_utc')},ensure_ascii=False))
    return summary


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--report',required=True)
    ap.add_argument('--past-days',type=int,default=7)
    ap.add_argument('--future-days',type=int,default=16)
    args=ap.parse_args()
    audit_and_clean(Path(args.input), Path(args.output), Path(args.report),
                    past_days=args.past_days, future_days=args.future_days)