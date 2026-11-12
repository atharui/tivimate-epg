"""Test that overlapping wrong titles, invalid times and duplicates cannot ship."""
import gzip
import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from xml.etree import ElementTree as ET
from epg_quality import audit_and_clean, timestamp

class QualityTests(unittest.TestCase):
 def test_timezone(self):
  self.assertEqual(timestamp('20261106170000 +0300'),timestamp('20261106140000 +0000'))
  self.assertEqual(timestamp('202611061400 -0000'),timestamp('202611061400 +0000'))
  self.assertIsNone(timestamp('20261106140000'))
 def test_remove_bad_programmes_and_keep_good(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);raw=d/'raw.xml.gz';clean=d/'clean.xml.gz';report=d/'report.json'
   xml='''<tv><channel id="kids"><display-name>Baraem</display-name></channel>
   <programme start="20261106140000 +0000" stop="20261106143000 +0000" channel="kids"><title>Cartoon A</title></programme>
   <programme start="20261106140000 +0000" stop="20261106143000 +0000" channel="kids"><title>Cartoon A</title></programme>
   <programme start="20261106141500 +0000" stop="20261106144500 +0000" channel="kids"><title>Unrelated news</title></programme>
   <programme start="20261106150000 +0000" stop="20261106140000 +0000" channel="kids"><title>Invalid</title></programme>
   <programme start="20261106160000 +0000" stop="20261106163000 +0000" channel="kids"><title>Cartoon B</title></programme>
   <programme start="20261001160000 +0000" stop="20261001163000 +0000" channel="kids"><title>Stale</title></programme>
   </tv>'''
   with gzip.open(raw,'wb') as o:o.write(xml.encode())
   result=audit_and_clean(raw,clean,report,now=datetime(2026,11,6,17,tzinfo=timezone.utc), max_loss=.9)
   self.assertEqual(result['input_programmes'],6)
   self.assertEqual(result['duplicate_programmes'],1)
   self.assertEqual(result['invalid_duration'],1)
   self.assertEqual(result['outside_useful_window'],1)
   self.assertEqual(result['contradictory_programme_records'],2)
   self.assertEqual(result['output_programmes'],1)
   with gzip.open(clean) as x:root=ET.parse(x).getroot()
   self.assertEqual([t.text for t in root.iter('title')],['Cartoon B'])
 def test_reject_overloss(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d)
   with gzip.open(d/'a.gz','wb') as w:w.write(b'<tv><channel id="a"><display-name>A</display-name></channel><programme start="20261106140000 +0000" stop="20261106130000 +0000" channel="a"><title>Wrong</title></programme></tv>')
   with self.assertRaises(ValueError):audit_and_clean(d/'a.gz',d/'b.gz',d/'rep.json',now=datetime(2026,11,6,tzinfo=timezone.utc))
if __name__ == '__main__':unittest.main()