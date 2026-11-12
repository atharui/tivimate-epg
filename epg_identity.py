"""Conservative identity audit for IPTV playlist-to-XMLTV matching.

This detects risks in a provider's labels; it does not infer true broadcast content.
Every result is a recommendation for manual verification, not a guessed schedule.
"""
from collections import defaultdict
import re
import unicodedata

COUNTRY_RE = re.compile(r'^(?:US|USA|UK|DE|FR|ES|IT|AR|SA|TR|NL|BE|RO|PL|AT|SE|NO|DK|RU|PT|CH|HU|AL|FI|GR|EG|AE)\s*:\s*',re.I)
QUALITY = frozenset({'hd','fhd','sd','uhd','4k','8k','hevc','h265','h264','1080p','720p','2160p','50fps','60fps'})
SHIFT_RE = re.compile(r'\b(?:EASTERN|PACIFIC|EAST|WEST|ET|PT|DELAYED)\b|(?:\+\s*[1-9]\b)',re.I)
REGIONAL_RE = re.compile(r'\b(?:ORF\s*(?:2|II)\s*[BKNOSTVW]|WDR\b.*(?:BIELEFELD|DORTMUND|DUISBURG|DUSSELDORF|DUESSELDORF|ESSEN)|RTL\s+(?:HH\s*SH|REGIONAL\s*NRW))\b',re.I)
TEAM_FEED_RE = re.compile(r'\bNFL\s+TEAMS?\s*:',re.I)
EVENT_RE = re.compile(r'\b(?:PPV\s+EVENTS?|EVENT\s*\d+)\b',re.I)
TVLAND_RE = re.compile(r'\bTV\s*LAND\b',re.I)
LOCAL_CALL_RE = re.compile(r'\b[WK][A-Z]{2,4}\b')


def clean_label(label):
    """Identity comparison keeps network, subchannel, region and feed name."""
    x=COUNTRY_RE.sub('', (label or '').split('◉',1)[0]).lower()
    x=unicodedata.normalize('NFKD',x)
    x=''.join(c for c in x if not unicodedata.combining(c))
    x=x.replace('&',' and ')
    x=re.sub(r'[^\w+]+', ' ',x)
    words=x.split()
    words=['sport' if w=='sports' else '2' if w=='ii' and 'orf' in words else w for w in words]
    words=[w for w in words if w not in QUALITY]
    # R and T are known provider marketing postfixes on some streams.
    if words and words[-1] in ('r','t'):
        words=words[:-1]
    return ' '.join(words)


def token_compatibility(a,b):
    """Prevent treating unrelated networks/events as the same TV schedule."""
    aa=clean_label(a);bb=clean_label(b)
    if not aa or not bb:return False
    if aa==bb:return True
    ta=set(aa.split());tb=set(bb.split())
    # Names like 'beIN LaLiga 1' vs 'beIN Sports 1' are deliberately different.
    if ('laliga' in ta) != ('laliga' in tb):return False
    if ('premierleague' in ta or 'primerliege' in ta) != ('premierleague' in tb or 'primerliege' in tb):return False
    if ('serie' in ta and 'a' in ta) != ('serie' in tb and 'a' in tb):return False
    # A localized variant is not equivalent to its national station ID.
    if SHIFT_RE.search(aa) or SHIFT_RE.search(bb):
        return aa==bb
    # Be conservative: strings with a different number are not the same station.
    na=set(re.findall(r'\b\d+\b',aa));nb=set(re.findall(r'\b\d+\b',bb))
    if na != nb:return False
    # 'Warner TV Comedy' and 'Warner Comedy' can share their programme guide.
    if ta-{'tv','channel'} == tb-{'tv','channel'}:return True
    return False


def id_label_mismatch(row):
    """If the provider's tvg-id unambiguously names another branded feed, flag it."""
    channel=clean_label(row.get('ChannelName',''))
    eid=(row.get('EPGChannelID') or '').lower()
    if not eid:return False
    if 'bein' in channel and 'bein' in eid:
        cid=re.search(r'\b(?:sport|sports)\s*(\d+)\b',channel)
        sid=re.search(r'(?:bein)?sports?(?:xtra)?(\d+)',eid.replace('.',''))
        if cid and sid and cid.group(1)!=sid.group(1):return True
        if cid and 'series' in eid:return True
        if re.search(r'\b(?:la\s*liga|laliga)\b',channel) and 'sports' in eid:return True
        if 'primerliege' in channel and 'sports' in eid:return True
        if 'serie a' in channel and 'sports' in eid:return True
        a=re.search(r'\bxtra\s*(\d+)\b',channel)
        b=re.search(r'sportsxtra(\d+)',eid.replace('.',''))
        if a and b and a.group(1)!=b.group(1):return True
    return False


def feed_variant_risk(row):
    """True matching needs a provider-confirmed feed, not just a similar name."""
    label=row.get('ChannelName','')
    if TEAM_FEED_RE.search(label):return 'NFL_TEAM_EVENT_FEED'
    if EVENT_RE.search(label):return 'EVENT_SCHEDULE_UNVERIFIED'
    if row.get('Region')=='USA' and TVLAND_RE.search(label) and not SHIFT_RE.search(label) and not row.get('EPGChannelID'):
        return 'TVLAND_FEED_UNSPECIFIED'
    if REGIONAL_RE.search(label):return 'REGIONAL_PROGRAMME_VARIANT'
    if SHIFT_RE.search(label) and not row.get('EPGChannelID'):
        return 'TIMESHIFT_FEED_NEEDS_VERIFICATION'
    return ''


def provider_id_collisions(rows):
    """Find IDs reused by labels that do not all denote the same broadcast."""
    byid=defaultdict(list)
    for i,row in enumerate(rows):
        eid=(row.get('EPGChannelID') or '').strip().casefold()
        if eid:byid[eid].append((i,row))
    risky={}
    for eid, entries in byid.items():
        if len(entries)<2:continue
        diverse=[]
        for _,row in entries:
            name=row['ChannelName']
            if not any(token_compatibility(name,prev) for prev in diverse):diverse.append(name)
        if len(diverse)>1:
            risky[eid]=[{'row':i,'name':row['ChannelName']} for i,row in entries]
    return risky


def reason_for_row(row,collisions):
    flags=[]
    feed=feed_variant_risk(row)
    if feed:flags.append(feed)
    if id_label_mismatch(row):flags.append('PROVIDER_ID_WRONG_STATION')
    eid=(row.get('EPGChannelID') or '').strip().casefold()
    if eid and eid in collisions:flags.append('SHARED_ID_DISTINCT_CHANNELS')
    return flags