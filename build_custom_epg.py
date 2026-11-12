#!/usr/bin/env python3
"""Build a targeted XMLTV guide from independently published programme data.

Run in directory containing Channels_US_Europe_Arabic.csv.
No subscription credentials, stream URLs or private IPTV APIs are used.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import concurrent.futures
import csv
import difflib
import gzip
import io
import os
from pathlib import Path
import re
import shutil
import time
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

BASE='https://epgshare01.online/epgshare01/'
EU_SOURCES={
  'AL':['AL1'],'AT':['AT1'],'BA':['BA1'],'BE':['BE2'],'BG':['BG1'],
  'CH':['CH1'],'CR':['HR1'],'CZ':['CZ1'],'DE':['DE1','DE_SKY','DE_MAGENTA','DE_ORG'],'DK':['DK1'],'ES':['ES1','ES_ORG'],
  'FI':['FI1'],'FR':['FR1','FR_ORG'],'GR':['GR1'],'HU':['HU1'],'IT':['IT1','IT_ORG'],'MK':['RS1'],
  'NL':['NL1'],'NO':['NO1'],'PL':['PL1'],'PT':['PT1'],'RO':['RO1','RO2'],
  'SE':['SE1'],'SK':['SK1'],'SR':['RS1'],'TR':['TR1','TR3'],'UA':['UA1'],
  'UK':['UK1','GB_ORG'],'BH':['BA1'],'ARM':['AM1'],'CRN':['ME_ORG'],'EN':['UK1'],
  'RU':['RU_ORG'],
}
AR_SOURCES=['AE1','BEIN1','ALJAZEERA1','SA2','SA1','EG1','BEIN_WEB','AE_ORG','EG_ORG','LB_ORG','ARABIC_GUIDE']
US_SOURCES=['US2','US_LOCALS1','US_SPORTS1','PEACOCK1','US_ORG','PLEX1','RAKUTEN1','DISTROTV1']
# Extra source lists are only requested if categories in user's CSV need them.
SPECIAL_URLS={'RU_ORG':'https://iptv-epg.org/files/epg-ru.xml.gz',
              'ME_ORG':'https://iptv-epg.org/files/epg-me.xml.gz',
              'US_ORG':'https://iptv-epg.org/files/epg-us.xml.gz',
              'GB_ORG':'https://iptv-epg.org/files/epg-gb.xml.gz',
              'DE_ORG':'https://iptv-epg.org/files/epg-de.xml.gz',
              'FR_ORG':'https://iptv-epg.org/files/epg-fr.xml.gz',
              'IT_ORG':'https://iptv-epg.org/files/epg-it.xml.gz',
              'ES_ORG':'https://iptv-epg.org/files/epg-es.xml.gz',
              'BEIN_WEB':'https://m3u-edit.com/epg-source.php?file=bein.com.xml',
              'DE_SKY':'https://m3u-edit.com/epg-source.php?file=germany_sky.de.xml',
              'DE_MAGENTA':'https://m3u-edit.com/epg-source.php?file=germany_web.magentatv.de.xml',
              'AM1':'https://iptv-epg.org/files/epg-am.xml.gz',
              'AE_ORG':'https://iptv-epg.org/files/epg-ae.xml.gz',
              'EG_ORG':'https://iptv-epg.org/files/epg-eg.xml.gz',
              'LB_ORG':'https://iptv-epg.org/files/epg-lb.xml.gz',
              'ARABIC_GUIDE':'https://raw.githubusercontent.com/GhalebAldoboni/EPG-Guide/master/ArabicEPG.xml',
              'AL_ORG':'https://iptv-epg.org/files/epg-al.xml.gz',
              'AT_ORG':'https://iptv-epg.org/files/epg-at.xml.gz',
              'BE_ORG':'https://iptv-epg.org/files/epg-be.xml.gz',
              'NL_ORG':'https://iptv-epg.org/files/epg-nl.xml.gz',
              'PL_ORG':'https://iptv-epg.org/files/epg-pl.xml.gz',
              'RO_ORG':'https://iptv-epg.org/files/epg-ro.xml.gz',
              'SE_ORG':'https://iptv-epg.org/files/epg-se.xml.gz',
              'TR_ORG':'https://iptv-epg.org/files/epg-tr.xml.gz',
              'UA_ORG':'https://iptv-epg.org/files/epg-ua.xml.gz',
              'PT_ORG':'https://iptv-epg.org/files/epg-pt.xml.gz',
              'GR_ORG':'https://iptv-epg.org/files/epg-gr.xml.gz',
              'BA_ORG':'https://iptv-epg.org/files/epg-ba.xml.gz',
              'RS_ORG':'https://iptv-epg.org/files/epg-rs.xml.gz'}
# Additional country guides are based on the countries represented in the user's playlist.
EXTRA_EU={'AL':'AL_ORG','AT':'AT_ORG','BE':'BE_ORG','NL':'NL_ORG','PL':'PL_ORG',
          'RO':'RO_ORG','SE':'SE_ORG','TR':'TR_ORG','UA':'UA_ORG',
          'PT':'PT_ORG','GR':'GR_ORG','BA':'BA_ORG','SR':'RS_ORG'}
HTTP_HEADERS={'User-Agent':'Mozilla/5.0 (compatible; LocalTVGuideBuilder/2.0)', 'Accept':'*/*'}
REMOVE_TOKENS={'hd','fhd','uhd','4k','8k','sd','hevc','h265','h264','3840','1080','720','50fps','60fps',
               'iptv','live','tv','channel','stream','en','vip','ultra','raw'}
IGNORE_FUZZY={'abc','nbc','cbs','fox','the','one','itv','be','sports','sky','ppv','event','now','4k','1','2'}

def normalize(s):
    s=(s or '').strip()
    s=unicodedata.normalize('NFKD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    s=re.sub(r'^[A-Z]{2,5}\s*:\s*','',s.strip(),flags=re.I)
    s=re.sub(r'\b(?:US|UK|DE|FR|ES|IT|AR|TR|NL|BE|RO|PL|AT|SE|NO|DK|RU|SA|HD|FHD|UHD|4K|8K|1080P|720P|HEVC|H265|H264|50FPS|60FPS)\s*[:|]\s*',' ',s,flags=re.I)
    s=re.sub(r'\s*(?:◉|⚽|♦|♬|\[MULTI AUDIO\])\s*',' ',s,flags=re.I)
    s=s.replace('&',' and ')
    s=re.sub(r'(?i)\b(?:4K|8K|2160P|1080P|720P|50FPS|60FPS)\b',' ',s)
    s=re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',s)
    s=re.sub(r'[^\w\u0600-\u06ff]+',' ',s.lower())
    words=[w for w in s.split() if w not in REMOVE_TOKENS]
    # Singular/plural spelling and common official broadcaster spacing.
    words=['sport' if w=='sports' else w for w in words]
    return ' '.join(words)

def epg_id_as_name(s):
    # Most EPGShare IDs encode a human-readable display name, before the country suffix.
    s=s.rsplit('.',1)[0].replace('.', ' ')
    return normalize(s)

def name_variants(s):
    """Use independently visible Latin and Arabic channel names, never stream metadata."""
    parts=(s or '').split('◉')
    result=[]
    for part in parts:
        n=normalize(part)
        if n and n not in result:result.append(n)
    # Common broadcaster spellings; safe only when exact after normalization.
    for n in list(result):
        for a,b in [('aljazeera','al jazeera'),('al arabiya','alarabiya'),
                    ('abu dhabi','abudhabi'),('al jazira','al jazeera'),
                    ('bein','be in')]:
            if a in n:
                alias=n.replace(a,b)
                if alias not in result:result.append(alias)
    return result

def select_identical_station(row,candidates):
    """Resolve same-channel/HD aliases across providers without guessing US local affiliates."""
    candidates=list(dict.fromkeys(candidates))
    name=row['ChannelName']
    sigs=callsign(name) if row['Region']=='USA' else set()
    # Even a single source candidate can be the wrong local affiliate.
    if sigs:
        candidates=[c for c in candidates if not callsign(c[1]) or callsign(c[1]) & sigs]
    if not candidates:return None
    if len(candidates)==1:return candidates[0]
    # Distinct US callsigns are different stations with different schedules.
    if row['Region']=='USA':
        if sigs:
            subset=[c for c in candidates if callsign(c[1]) & sigs]
            if subset:candidates=subset
        else:
            sigs_in_sources={frozenset(callsign(c[1])) for c in candidates if callsign(c[1])}
            if len(sigs_in_sources)>1:return None
    if len(candidates)==1:return candidates[0]
    rank={source:i for i,source in enumerate(country_sources(row))}
    # Keep formerly preferred sources first; do not override an existing match.
    candidates.sort(key=lambda c:(rank.get(c[0],999),
        0 if ('HD' in name.upper() and re.search(r'\bhd\b',c[1],re.I)) else 1,
        len(c[1]),c[1]))
    best=candidates[0]
    # Inside the preferred source, genuinely different names/feeds remain ambiguous.
    same_source=[c for c in candidates if c[0]==best[0]]
    roots={normalize(epg_id_as_name(c[1])) for c in same_source}
    return best if len(roots)<=1 else None

def callsign(s):
    # Local US affiliates: station callsign distinguishes cities and time zones.
    return {x for x in re.findall(r'\b[WK][A-Z]{2,4}\b',(s or '').upper()) if x not in {'WEST','KIDS','WIDE'}}

def urlopen(url,timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url,headers=HTTP_HEADERS),timeout=timeout)

def fetch_binary(url,dest):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size>50 and (time.time()-dest.stat().st_mtime)<12*3600:
        return dest
    tmp=dest.with_suffix(dest.suffix+'.partial')
    try:
        with urlopen(url,60) as src,open(tmp,'wb') as out:
            shutil.copyfileobj(src,out,1024*256)
        if tmp.stat().st_size<100: raise IOError('Downloaded file unexpectedly small')
        tmp.replace(dest)
    finally:
        if tmp.exists():tmp.unlink()
    return dest

def xml_open(path):
    with open(path,'rb') as r:
        zipped=r.read(2)==b'\x1f\x8b'
    return gzip.open(path,'rb') if zipped else open(path,'rb')

def read_xml_index(path):
    result=[]
    with xml_open(path) as fh:
        context=ET.iterparse(fh,events=('start','end'))
        root=None
        for event,elem in context:
            if root is None and event=='start':root=elem
            if event=='end' and elem.tag=='channel':
                id_=elem.get('id','')
                names=[x.text for x in elem.findall('display-name') if x.text]
                if id_:result.append((id_,names))
                elem.clear()
                if root is not None:root.clear()
            elif event=='end' and elem.tag=='programme':
                elem.clear()
                if root is not None:root.clear()
    return result

def index_one(source,cache):
    try:
        if source in SPECIAL_URLS:
            xmlfile=fetch_binary(SPECIAL_URLS[source],cache/(source+'.xml.gz'))
            return source,read_xml_index(xmlfile),None
        url=BASE+'epg_ripper_'+source+'.txt'
        file=fetch_binary(url,cache/(source+'.txt'))
        contents=file.read_text(encoding='utf-8-sig',errors='replace')
        ids=[line.strip() for line in contents.splitlines() if line.strip() and not line.startswith('--') and not re.fullmatch(r'\d{10,14}',line.strip())]
        return source,[(x,[epg_id_as_name(x)]) for x in ids],None
    except Exception as ex:return source,[],str(ex)

def country_sources(row):
    region=row['Region'];code=row['CountryCode']
    if region=='USA':return US_SOURCES
    if region=='EUROPE':
        found=list(EU_SOURCES.get(code,['UK1']))
        extra=EXTRA_EU.get(code)
        if extra and extra not in found:found.append(extra)
        return found
    if region=='ARABIC':return AR_SOURCES
    return []

def index_by_name(catalog):
    by_exact=defaultdict(list);by_norm=defaultdict(list);by_first=defaultdict(list);by_call=defaultdict(list)
    for source,entries in catalog.items():
        for id_,names in entries:
            obj=(source,id_)
            by_exact[id_.lower()].append(obj)
            for name in list(names)+[epg_id_as_name(id_)]:
                for n in name_variants(name):
                    if not n:continue
                    if obj not in by_norm[n]:by_norm[n].append(obj)
                    first=n.split()[0]
                    if obj not in by_first[first]:by_first[first].append(obj)
                for sig in callsign(id_+' '+name):
                    if obj not in by_call[sig]:by_call[sig].append(obj)
    return by_exact,by_norm,by_first,by_call

def provider_id_mismatch(row):
    """Known unsafe provider mapping: different beIN station number/type in tvg-id."""
    cid=(row.get('EPGChannelID') or '').strip().lower()
    name=(row.get('ChannelName') or '').upper()
    if not cid:return False
    num=re.search(r'BEIN\s+SPORTS?\s+XTRA\s*(\d+)\b',name)
    ref=re.search(r'beinsportsxtra(\d+)',cid)
    if num and ref and num.group(1)!=ref.group(1):return True
    if re.search(r'\bBEIN\s+SPORTS?\s+\d+\b',name) and 'beinseries' in cid:return True
    return False


def pick_match(row,idx):
    exact,by_norm,by_first,by_call=idx
    allowed=set(country_sources(row))
    eid=(row['EPGChannelID'] or '').strip().lower()
    if eid:
        same=[c for c in exact.get(eid,[]) if c[0] in allowed]
        if same:
            chosen=select_identical_station(row,same)
            if chosen:return chosen, 'EXACT_ID'
    variants=name_variants(row['ChannelName'])
    for n in variants:
        same=[c for c in by_norm.get(n,[]) if c[0] in allowed]
        if same:
            chosen=select_identical_station(row,same)
            if chosen:return chosen, 'EXACT_NAME'
    if row['Region']=='USA':
        signatures=callsign(row['ChannelName'])
        if signatures:
            # A unique American station callsign is much safer than a network label.
            matches=set()
            for sig in signatures:
                matches.update(c for c in by_call.get(sig,[]) if c[0] in allowed)
            chosen=select_identical_station(row,matches)
            if chosen and callsign(chosen[1]) & signatures:
                return chosen,'US_CALLSIGN'
    if not variants:return None,'NO_SAFE_MATCH'
    for n in variants:
        if len(n)<4:continue
        tokens=n.split()
        if not tokens or (len(tokens)==1 and tokens[0] in IGNORE_FUZZY):continue
        choices=[c for c in by_first.get(tokens[0],[]) if c[0] in allowed]
        if not choices or len(choices)>100:continue
        scores=[]
        for source,cid in choices:
            cn=epg_id_as_name(cid)
            score=difflib.SequenceMatcher(None,n,cn).ratio()
            if score>=.96:scores.append((score,(source,cid)))
        if not scores:continue
        scores.sort(key=lambda x:x[0],reverse=True)
        top=[c for score,c in scores if scores[0][0]-score<=.015]
        chosen=select_identical_station(row,top)
        if chosen and (len(scores)==len(top) or scores[0][0]-scores[len(top)][0]>=.07):
            return chosen,'HIGH_CONFIDENCE_NAME'
    return None,'NO_SAFE_MATCH'

def output_id(row,matched):
    return row['EPGChannelID'].strip() or matched[1]

def write_csv(path,rows,fields):
    with open(path,'w',encoding='utf-8-sig',newline='') as out:
        w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def merge_guide(srcfile,source_to_ids,out,programme_counts):
    kept=0
    with xml_open(srcfile) as fh:
        context=ET.iterparse(fh,events=('start','end'))
        root=None
        for event,elem in context:
            if root is None and event=='start':root=elem
            if event!='end':continue
            if elem.tag=='programme':
                source_id=elem.get('channel','')
                ids=source_to_ids.get(source_id)
                if ids:
                    for target_id in ids:
                        elem.set('channel',target_id)
                        out.write(ET.tostring(elem,encoding='utf-8')+b'\n')
                        programme_counts[target_id]+=1;kept+=1
                elem.clear()
                if root is not None:root.clear()
            elif elem.tag=='channel':
                elem.clear()
                if root is not None:root.clear()
    return kept

def quarantine_ambiguous_ids(matched_sources,report):
    """Never choose one arbitrary source if a target ID points to different stations."""
    usages=defaultdict(set)
    for src,groups in matched_sources.items():
        for source_id,ids in groups.items():
            for final_id in ids:
                usages[final_id].add((src,source_id))
    conflicted={eid for eid,mappings in usages.items() if len(mappings)>1}
    if conflicted:
        for groups in matched_sources.values():
            for ids in groups.values():
                ids.difference_update(conflicted)
        for row in report:
            if row.get('FinalEPGID') in conflicted:
                row['MatchStatus']='UNMATCHED'
                row['MatchMethod']='CONFLICTING_SOURCE_ID'
                row['TiviMateAction']='Multiple different source schedules reuse the same EPG ID; manual verification required'
                row['FinalEPGID']=''
    return conflicted


def add_tv_land_pacific_option(rows, catalog, matched_sources, channel_names):
    """Expose an explicit Pacific choice without guessing the subscriber's coast.

    The default TV Land East schedule remains unchanged. This adds a *separate*
    XMLTV ID users can choose via TiviMate's Assign EPG when their live TV feed
    is the Pacific version. The West ID must actually exist in the US2 index.
    """
    has_tv_land=any(
        row.get('Region')=='USA' and
        re.search(r'\bTV\s+LAND\b',row.get('ChannelName',''),flags=re.I)
        for row in rows
    )
    if not has_tv_land:
        return False
    pacific_id='TV.Land.HD.(Pacific).us2'
    if not any(entry_id==pacific_id for entry_id,_ in catalog.get('US2',[])):
        return False
    # The Pacific listing has its own distinct EPG channel ID.
    matched_sources['US2'][pacific_id].add(pacific_id)
    channel_names[pacific_id]=[
        'TV Land HD (Pacific)',
        'TV LAND WEST',
        'TV Land — Pacific feed'
    ]
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',default='Channels_US_Europe_Arabic.csv')
    ap.add_argument('--outdir',default='.')
    args=ap.parse_args()
    parent=Path(__file__).resolve().parent
    inpath=Path(args.input) if Path(args.input).is_absolute() else parent/args.input
    outdir=Path(args.outdir) if Path(args.outdir).is_absolute() else parent/args.outdir
    outdir.mkdir(parents=True,exist_ok=True);cache=outdir/'_source_cache';cache.mkdir(exist_ok=True)
    with open(inpath,encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    sources=sorted({s for row in rows for s in country_sources(row)})
    print(f'Input: {len(rows):,} channels | {len(sources)} public source feeds')
    print('Fetching channel indexes (does NOT contact your IPTV subscription)...')
    cat={};errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for future in concurrent.futures.as_completed([pool.submit(index_one,s,cache) for s in sources]):
            src,ids,err=future.result()
            if err:errors.append((src,err));print('  UNAVAILABLE',src,err[:100]);continue
            cat[src]=ids;print('  INDEX',src,len(ids))
    if not cat:raise SystemExit('No public EPG indexes were available; nothing has been fabricated.')
    idx=index_by_name(cat)
    report=[]; matched_sources=defaultdict(lambda:defaultdict(set)); counts=Counter(); conflicts=defaultdict(set)
    for row in rows:
        if provider_id_mismatch(row):
            matched,reason=None,'PROVIDER_ID_MISMATCH'
        else:
            matched,reason=pick_match(row,idx)
        new=dict(row)
        new['MatchStatus']='MATCHED' if matched else 'UNMATCHED'
        new['MatchMethod']=reason
        new['GuideSource']=matched[0] if matched else ''
        new['SourceGuideID']=matched[1] if matched else ''
        new['FinalEPGID']=output_id(row,matched) if matched else ''
        new['TiviMateAction']=('Automatic ID match is possible' if row['EPGChannelID'] else 'May require Assign EPG in TiviMate') if matched else 'No verified schedule; manual review needed'
        if reason=='PROVIDER_ID_MISMATCH':
            new['TiviMateAction']='IPTV provider tvg-id belongs to a different station; fix playlist or Assign EPG manually'
        report.append(new);counts[(row['Region'],new['MatchStatus'])]+=1
        if matched:
            conflicts[new['FinalEPGID']].add((matched[0],matched[1]))
            matched_sources[matched[0]][matched[1]].add(new['FinalEPGID'])
    conflict_ids=quarantine_ambiguous_ids(matched_sources,report)
    if conflict_ids:
        print(f'WARNING: {len(conflict_ids)} EPG IDs point to different sources; quarantined all conflicting mappings.')
    counts=Counter((r['Region'],r['MatchStatus']) for r in report)
    fields=list(rows[0])+['MatchStatus','MatchMethod','GuideSource','SourceGuideID','FinalEPGID','TiviMateAction']
    write_csv(outdir/'EPG_Match_Report.csv',report,fields)
    print('Match status by region:')
    for reg in ('USA','EUROPE','ARABIC'):
        print(f'  {reg}: matched={counts[(reg,"MATCHED")]:,}, unmatched={counts[(reg,"UNMATCHED")]:,}')
    # Only real programme data is written. No synthetic/fake events.
    epg=outdir/'Custom_EPG.xml.gz';programme_counts=Counter();failed_sources=[]
    with gzip.open(epg,'wb',compresslevel=6) as out:
        out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="Personal guide-merge v2">\n')
        # Distinct streams (SD/HD/4K) can share one verified schedule. Retain all
        # display-name aliases so TiviMate can find the right channel by its name.
        channel_names=defaultdict(list)
        for row in report:
            if row['MatchStatus']!='MATCHED':continue
            key=row['FinalEPGID']
            aliases=[row['ChannelName']]
            if '◉' in row['ChannelName']:
                aliases.append(row['ChannelName'].split('◉',1)[1].strip())
            for alias in aliases:
                if alias and alias not in channel_names[key] and len(channel_names[key])<48:
                    channel_names[key].append(alias)
        if add_tv_land_pacific_option(rows,cat,matched_sources,channel_names):
            print('  TV LAND: kept Eastern default; added distinct Pacific guide for manual Assign EPG')
        for id_,names in channel_names.items():
            elem=ET.Element('channel',id=id_)
            for name in names:ET.SubElement(elem,'display-name').text=name
            out.write(ET.tostring(elem,encoding='utf-8')+b'\n')
        for src,groups in matched_sources.items():
            if not any(groups.values()):continue
            try:
                if src in SPECIAL_URLS:srcfile=cache/(src+'.xml.gz')
                else:srcfile=fetch_binary(BASE+'epg_ripper_'+src+'.xml.gz',cache/(src+'.xml.gz'))
                n=merge_guide(srcfile,groups,out,programme_counts)
                print(f'  PROGRAMMES {src}: {n:,}')
            except Exception as ex:
                failed_sources.append((src,str(ex)));print(f'  FAILED programme download {src}: {ex}')
        out.write(b'</tv>\n')
    for row in report:
        row['AvailableProgrammes']=str(programme_counts[row['FinalEPGID']]) if row['FinalEPGID'] else '0'
        if row['FinalEPGID'] and not programme_counts[row['FinalEPGID']]:row['MatchStatus']='NO_CURRENT_PROGRAMMES'
    write_csv(outdir/'EPG_Match_Report.csv',report,fields+['AvailableProgrammes'])
    with open(outdir/'EPG_Summary.txt','w',encoding='utf-8') as f:
        f.write('EPG build — verified public source data only\n')
        f.write(f'Input channels: {len(rows)}\n')
        for region in ('USA','EUROPE','ARABIC'):
            group=[r for r in report if r['Region']==region]
            actual=sum(int(r['AvailableProgrammes'])>0 for r in group)
            f.write(f'{region}: total {len(group)}; with actual programme listings {actual}; remaining {len(group)-actual}\n')
        f.write(f'Programme rows written: {sum(programme_counts.values())}\n')
        f.write('Unavailable sources: '+', '.join(x[0] for x in errors+failed_sources)+'\n')
        f.write('IMPORTANT: Channels without an EPGChannelID may require manual Assign EPG in TiviMate.\n')
        f.write('Local TV affiliates differ by city. No unsupported schedule was invented.\n')
    print('DONE:',epg)
    print('IMPORTANT: a positive matching result is not equivalent to TiviMate auto-matching when the playlist ID is blank.')
    print('See EPG_Match_Report.csv and EPG_Summary.txt in the script folder')

if __name__=='__main__':main()