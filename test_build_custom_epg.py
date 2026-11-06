"""Offline regression tests; do not require IPTV credentials or network access."""
import unittest
from collections import defaultdict
import build_custom_epg as guide

class ChannelMatchingTests(unittest.TestCase):
    def test_arabic_display_names(self):
        self.assertIn('ابو ظبي', guide.name_variants('ABU DHABI HD ◉ ابو ظبي'))
        self.assertIn('ad sport 1', guide.name_variants('AD SPORT 1 HD'))

    def test_country_extras(self):
        self.assertIn('TR_ORG',guide.country_sources({'Region':'EUROPE','CountryCode':'TR'}))
        self.assertIn('EG_ORG',guide.country_sources({'Region':'ARABIC','CountryCode':'AE'}))

    def test_prefer_existing_for_same_station(self):
        row={'Region':'ARABIC','CountryCode':'AE','ChannelName':'ABU DHABI HD'}
        options=[('AE_ORG','Abu.Dhabi.HD.ae'),('AE1','Abu.Dhabi.HD.ae')]
        self.assertEqual(guide.select_identical_station(row,options)[0],'AE1')

    def test_do_not_invent_local_us_affiliate(self):
        row={'Region':'USA','CountryCode':'US','EPGChannelID':'','ChannelName':'US: ABC'}
        self.assertIsNone(guide.select_identical_station(row,[('US_LOCALS1','KABC.us'),('US_LOCALS1','WABC.us')]))

    def test_match_us_callsign(self):
        row={'Region':'USA','CountryCode':'US','EPGChannelID':'','ChannelName':'US: ABC (KABC)'}
        ids={'US_LOCALS1':[('WABC.us',['WABC']),('KABC.us',['KABC'])]}
        match,kind=guide.pick_match(row,guide.index_by_name(ids))
        self.assertEqual(match,('US_LOCALS1','KABC.us'))

    def test_no_sports_fake_schedule(self):
        row={'Region':'USA','CountryCode':'US','EPGChannelID':'','ChannelName':'US: PPV EVENT 48'}
        match,_=guide.pick_match(row,guide.index_by_name({'US2':[('ESPN.us',['ESPN'])]}))
        self.assertIsNone(match)

if __name__=='__main__':unittest.main()