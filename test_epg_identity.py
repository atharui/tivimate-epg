import unittest
from epg_identity import clean_label, token_compatibility, id_label_mismatch, feed_variant_risk, provider_id_collisions, reason_for_row

class PlaylistIdentityTests(unittest.TestCase):
    def test_tvland_generic_cannot_infer_coast(self):
        row={'Region':'USA','ChannelName':'USA: TV LAND HD','EPGChannelID':''}
        self.assertEqual(feed_variant_risk(row),'TVLAND_FEED_UNSPECIFIED')
    def test_tvland_explicit_east_not_ambiguous(self):
        row={'Region':'USA','ChannelName':'USA: TV LAND EAST','EPGChannelID':''}
        self.assertEqual(feed_variant_risk(row),'TIMESHIFT_FEED_NEEDS_VERIFICATION')
    def test_all_nfl_team_streams_are_not_normal_affiliates(self):
        row={'Region':'USA','ChannelName':'USA: NFL Teams: CBS Bengals (WKRC) Cincinnati OH','EPGChannelID':''}
        self.assertEqual(feed_variant_risk(row),'NFL_TEAM_EVENT_FEED')
    def test_do_not_flag_normal_local_fox(self):
        self.assertFalse(feed_variant_risk({'Region':'USA','ChannelName':'US: FOX 40 (KTXL) Sacramento HD','EPGChannelID':'foxktxl.us'}))
    def test_regional_wdr(self):
        self.assertEqual(feed_variant_risk({'Region':'EUROPE','ChannelName':'DE: WDR HD DORTMUND','EPGChannelID':'WDR.de'}),'REGIONAL_PROGRAMME_VARIANT')
    def test_provider_wrong_bein_brand(self):
        self.assertTrue(id_label_mismatch({'ChannelName':'AR: BEIN LALIGA 2 4K','EPGChannelID':'beINSports1.qa'}))
        self.assertTrue(id_label_mismatch({'ChannelName':'BEIN SPORTS 1 HD','EPGChannelID':'beinseries1.qa'}))
        self.assertTrue(id_label_mismatch({'ChannelName':'BEIN SPORTS XTRA 1 SD','EPGChannelID':'beINSportsXtra2.qa'}))
    def test_compatible_quality_variants(self):
        self.assertTrue(token_compatibility('IT: SKY SPORT F1 HD','IT: SKY SPORT F1 4K'))
        self.assertFalse(token_compatibility('AR: BEIN LALIGA 2 4K','BEIN SPORTS 1 HD'))
    def test_reused_id_collision_with_regional(self):
        rows=[{'ChannelName':'DE: WDR HD BIELEFELD','EPGChannelID':'WDR.de'},
              {'ChannelName':'DE: WDR HD DORTMUND','EPGChannelID':'WDR.de'}]
        conflicts=provider_id_collisions(rows)
        self.assertIn('wdr.de',conflicts)
        self.assertIn('SHARED_ID_DISTINCT_CHANNELS',reason_for_row(rows[0],conflicts))
    def test_plain_duplicates_no_collision(self):
        rows=[{'ChannelName':'IT: SKY SPORT F1 4K','EPGChannelID':'skysportf1.it'},
              {'ChannelName':'IT: SKY SPORT F1 HD','EPGChannelID':'skysportf1.it'}]
        self.assertFalse(provider_id_collisions(rows))
if __name__ == '__main__':unittest.main()