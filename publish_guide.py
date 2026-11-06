#!/usr/bin/env python3
"""Validate the newly generated guide and prepare the public static website.
Never publishes account credentials, URLs of IPTV streams, or raw provider IDs.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
import argparse
import gzip
import json
import shutil


def validate_and_publish(source: Path, destination: Path) -> dict:
    if not source.is_file():
        raise SystemExit('Guide missing; existing Pages deployment is preserved.')
    channels = programs = current = 0
    now = datetime.now(timezone.utc)
    with gzip.open(source, 'rb') as f:
        context = ET.iterparse(f, events=('start', 'end'))
        root = None
        for event, item in context:
            if root is None and event == 'start':
                if item.tag != 'tv':
                    raise SystemExit('Invalid XMLTV document')
                root = item
            if event != 'end':
                continue
            if item.tag == 'channel':
                channels += 1
            elif item.tag == 'programme':
                programs += 1
                # Sample one in 20 to avoid excess parsing overhead.
                if programs % 20 == 0:
                    try:
                        dt = datetime.strptime(item.attrib['start'][:20], '%Y%m%d%H%M%S %z')
                        if now - timedelta(hours=6) <= dt <= now + timedelta(days=16):
                            current += 1
                    except (KeyError, ValueError):
                        pass
            if item.tag in ('channel', 'programme'):
                item.clear()
                if root is not None:
                    root.clear()
    # Existing working local guide had 2,023 channel elements and 233,995 programs.
    # Block regressions and source errors instead of replacing a good deployment.
    if channels < 1500 or programs < 160000 or current < 100:
        raise SystemExit(f'VALIDATION FAILED: channels={channels}; programs={programs}; recent-sample={current}; previously deployed site is unchanged')

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination / 'guide.xml.gz')
    with gzip.open(source, 'rb') as inp, (destination / 'guide.xml').open('wb') as out:
        shutil.copyfileobj(inp, out, 1024 * 1024)
    (destination / '.nojekyll').write_text('', encoding='utf-8')
    summary = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'channel_ids': channels,
        'programmes': programs,
        'recent_future_sample_1_in_20': current,
        'note': 'Channel IDs with EPG listings; not all channels automatically bind in TiviMate.',
    }
    (destination / 'status.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (destination / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Personal XMLTV guide</title>
    <h1>Personal XMLTV guide</h1><p>Use the <a href="guide.xml">XMLTV guide</a> in TiviMate or the <a href="guide.xml.gz">compressed version</a>.</p>
    <p><a href="status.json">Build status</a></p></html>''', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', default='generated/Custom_EPG.xml.gz')
    parser.add_argument('--destination', default='site')
    args = parser.parse_args()
    validate_and_publish(Path(args.candidate), Path(args.destination))