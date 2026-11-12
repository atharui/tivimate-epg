"""Safety regression tests: don't publish a demonstrably different station's guide."""
import unittest
from collections import defaultdict
import build_custom_epg as guide

class StrictMappingTests(unittest.TestCase):
    def test_mismatched_bein_provider_id(self):
        for name,cid in [('BEIN SPORTS 1 HD','beinseries1.qa'),
                         ('BEIN SPORTS XTRA 1 SD','beINSportsXtra2.qa'),
                         ('BEIN SPORTS XTRA 2 SD','beINSportsXtra3.qa'),
                         ('BEIN SPORTS XTRA 4','beINSportsXtra3.qa')]:
            self.assertTrue(guide.provider_id_mismatch({'ChannelName':name,'EPGChannelID':cid}))
        self.assertFalse(guide.provider_id_mismatch({'ChannelName':'BEIN SPORTS XTRA 3 HD','EPGChannelID':'beinsportsxtra3.qa'}))
    def test_us_callsign_collision_rejected_even_single_candidate(self):
        row={'Region':'USA','CountryCode':'US','ChannelName':'US: ABC (KABC)','EPGChannelID':'WABC.us'}
        self.assertIsNone(guide.select_identical_station(row,[('US_LOCALS1','WABC.us')]))
    def test_conflicting_source_target_id_quarantined(self):
        grouped=defaultdict(lambda:defaultdict(set))
        grouped['US2']['KABC.us'].add('shared')
        grouped['US_LOCALS1']['WABC.us'].add('shared')
        rows=[{'Region':'USA','MatchStatus':'MATCHED','MatchMethod':'EXACT_ID','FinalEPGID':'shared', 'GuideSource':'US2','SourceGuideID':'KABC.us'},
              {'Region':'USA','MatchStatus':'MATCHED','MatchMethod':'EXACT_ID','FinalEPGID':'shared', 'GuideSource':'US_LOCALS1','SourceGuideID':'WABC.us'}]
        conflicts=guide.quarantine_ambiguous_ids(grouped,rows)
        self.assertEqual(conflicts,{'shared'})
        self.assertFalse(grouped['US2']['KABC.us'])
        self.assertFalse(grouped['US_LOCALS1']['WABC.us'])
        self.assertTrue(all(r['MatchStatus']=='UNMATCHED' for r in rows))

if __name__=='__main__': unittest.main()