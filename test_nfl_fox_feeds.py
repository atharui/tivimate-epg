"""NFL FOX market feeds should not inherit unrelated 24/7 local FOX schedules."""
import unittest
from collections import defaultdict
import build_custom_epg as g

class TeamFeedTests(unittest.TestCase):
    def test_quarantine_three_reported_streams(self):
        names=[
            'USA: NFL Teams: FOX Rams (KTXL) Sacramento CA',
            'USA: NFL Teams: FOX Redskins (WBFF) Baltimore MD',
            'USA: NFL Teams: FOX Redskins (WTTG) Washington DC',
        ]
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(g.is_unverified_nfl_fox_feed({'Region':'USA','ChannelName':name,'EPGChannelID':''}))

    def test_does_not_affect_real_fox_local_station(self):
        for name in ['US: FOX 5 (WTTG) Washington HD','US: FOX 40 KTXL','USA: NFL Teams: FOX Eagles (WTXF) Philadelphia PA']:
            self.assertFalse(g.is_unverified_nfl_fox_feed({'Region':'USA','ChannelName':name}))
        row={'Region':'USA','CountryCode':'US','ChannelName':'US: FOX 5 (WTTG) Washington HD','EPGChannelID':''}
        guide={'US_LOCALS1':[('WTTG-DT.us_locals1',['FOX 5 Washington WTTG'])]}
        picked,method=g.pick_match(row,g.index_by_name(guide))
        self.assertEqual(picked,('US_LOCALS1','WTTG-DT.us_locals1'))

    def test_separate_verifiable_station_options(self):
        ids=['KTXL-DT.us_locals1','WBFF-DT.us_locals1','WTTG-DT.us_locals1']
        catalog={'US_LOCALS1':[(id_,[]) for id_ in ids]}
        matched=defaultdict(lambda:defaultdict(set))
        names=defaultdict(list)
        total=g.add_nfl_fox_local_station_options(catalog,matched,names)
        self.assertEqual(total,3)
        for id_ in ids:
            self.assertEqual(matched['US_LOCALS1'][id_],{id_})
            self.assertEqual(len(names[id_]),1)
            self.assertNotIn('NFL',names[id_][0])

    def test_no_missing_source_fabrication(self):
        matched=defaultdict(lambda:defaultdict(set))
        names=defaultdict(list)
        self.assertEqual(g.add_nfl_fox_local_station_options({},matched,names),0)
        self.assertEqual(dict(matched),{})
        self.assertEqual(dict(names),{})

if __name__=='__main__':unittest.main()
