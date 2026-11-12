import gzip,csv,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from xml.etree import ElementTree as ET
import publish_guide as pg

class PublicationTests(unittest.TestCase):
 def test_coverage_uses_cleaned_programmes_not_old_csv_counts(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);base=p/'source';base.mkdir()
   xml='''<tv><channel id="a"><display-name>A</display-name></channel><programme start="20261112120000 +0000" stop="20261112130000 +0000" channel="a"><title>A</title></programme></tv>'''
   with gzip.open(base/'clean.gz','wb') as f:f.write(xml.encode())
   with (base/'EPG_Match_Report.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['Region','EPGChannelID','FinalEPGID','AvailableProgrammes']);w.writeheader()
    w.writerows([{'Region':'USA','EPGChannelID':'a','FinalEPGID':'a','AvailableProgrammes':'99'}, {'Region':'USA','EPGChannelID':'b','FinalEPGID':'b','AvailableProgrammes':'99'}])
   r=pg.validate_and_publish(base/'clean.gz',p/'site',min_channels=1,min_programmes=1,min_recent_sample=0)
   self.assertEqual(r['actual_listed_channels'],1)
   self.assertEqual(r['coverage_by_region']['USA']['without_programmes'],1)
 def test_orphan_programme_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   with gzip.open(p/'guide.gz','wb') as f:f.write(b'<tv><programme start="20261112120000 +0000" stop="20261112130000 +0000" channel="notfound"><title>Wrong</title></programme></tv>')
   with self.assertRaises(RuntimeError):pg.validate_and_publish(p/'guide.gz',p/'site',min_channels=0,min_programmes=1,min_recent_sample=0)
if __name__=='__main__':unittest.main()