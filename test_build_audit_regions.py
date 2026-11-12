"""Regression tests of safe matching across independent guide sources."""
import unittest
from collections import defaultdict
import build_custom_epg as b

class GuideSafety(unittest.TestCase):
    def test_generic_tvland_is_ambiguous_east_vs_pacific(self):
        row={'Region':'USA','CountryCode':'US','ChannelName':'USA: TV LAND HD','EPGChannelID':''}
        matched,reason=b.safe_match(row,b.index_by_name({'US2':[('TV.Land.HD.us2',['TV Land HD']),('TV.Land.HD.(Pacific).us2',['TV Land HD (Pacific)'])]}))
        self.assertIsNone(matched)
        self.assertEqual(reason,'TVLAND_FEED_UNSPECIFIED')
    def test_can_offer_all_verified_tvland_variants_without_auto_assign(self):
        rows=[{'ChannelName':'USA: TV LAND HD','Region':'USA','CountryCode':'US','EPGChannelID':''}]
        cat={'US2':[('TV.Land.HD.us2',[]),('TV.Land.HD.(Pacific).us2',[])]}
        src=defaultdict(lambda:defaultdict(set));names=defaultdict(list)
        count=b.add_tv_land_choices(rows,cat,src,names)
        self.assertEqual(count,2)
        self.assertEqual(src['US2']['TV.Land.HD.us2'],{'TV.Land.HD.us2'})
        self.assertEqual(src['US1']['TV.Land.-.Eastern.us'],{'TV.Land.-.Eastern.us'})
        self.assertNotIn('USA: TV LAND HD',sum(names.values(),[]))
    def test_all_nfl_team_feeds_quarantined(self):
        for name in ['USA: NFL Teams: FOX Rams (KTXL) Sacramento CA','USA: NFL Teams: CBS Bears (WBBM) Chicago IL']:
            row={'Region':'USA','CountryCode':'US','ChannelName':name,'EPGChannelID':''}
            got,reason=b.safe_match(row,b.index_by_name({'US_LOCALS1':[('KTXL-DT.us_locals1',['FOX 40']),('WBBM-DT.us_locals1',['CBS 2'])]}))
            self.assertIsNone(got)
            self.assertEqual(reason,'NFL_TEAM_EVENT_FEED')
    def test_real_local_fox_unaffected(self):
        row={'Region':'USA','CountryCode':'US','ChannelName':'US: FOX 40 (KTXL) Sacramento HD','EPGChannelID':'foxktxl.us'}
        got,reason=b.safe_match(row,b.index_by_name({'US_LOCALS1':[('KTXL-DT.us_locals1',['FOX 40 KTXL'])]}))
        self.assertEqual(got,('US_LOCALS1','KTXL-DT.us_locals1'))
    def test_bein_bad_id_blocked(self):
        row={'Region':'ARABIC','CountryCode':'AE','ChannelName':'AR: BEIN LALIGA 2 4K','EPGChannelID':'beINSports1.qa'}
        got,reason=b.safe_match(row,b.index_by_name({'AE1':[('beINSports1.qa',['beIN Sports 1'])]}))
        self.assertIsNone(got)
        self.assertEqual(reason,'PROVIDER_ID_WRONG_STATION')
    def test_country_source_us1_not_auto_assigned(self):
        sources=b.country_sources({'Region':'USA','CountryCode':'US'})
        self.assertNotIn('US1',sources)
        # A manual-only US1 source cannot influence other automatic matches.
        self.assertIn('US2',sources)
    def test_regional_wdr_no_generic_id(self):
        row={'Region':'EUROPE','CountryCode':'DE','ChannelName':'DE: WDR HD DORTMUND','EPGChannelID':'WDR.de'}
        got,reason=b.safe_match(row,b.index_by_name({'DE1':[('WDR.de',['WDR'])]}))
        self.assertIsNone(got)
        self.assertEqual(reason,'REGIONAL_PROGRAMME_VARIANT')

if __name__=='__main__':unittest.main()