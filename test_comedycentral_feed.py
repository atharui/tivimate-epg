"""A user-observed Comedy Central UK feed must not inherit the US listing."""
import unittest
import build_custom_epg as g

class ComedyCentralUKFeedTests(unittest.TestCase):
    def setUp(self):
        self.us={'Region':'USA','CountryCode':'US',
                 'ChannelName':'USA: COMEDY CENTRAL','EPGChannelID':'comedycentral.us'}
        self.idx=g.index_by_name({
            'US2':[('Comedy.Central.HD.us2',['Comedy Central HD'])],
            'UK1':[('ComedyCentral.uk',['Comedy Central'])]})

    def test_observed_uk_feed_uses_uk_schedule_under_original_provider_id(self):
        match,reason=g.safe_match(self.us,self.idx)
        self.assertEqual(match,('UK1','ComedyCentral.uk'))
        self.assertEqual(reason,'OBSERVED_UK_COMEDY_CENTRAL_FEED')
        self.assertEqual(g.output_id(self.us,match),'comedycentral.us')

    def test_does_not_rewrite_a_real_uk_entry(self):
        row={'Region':'EUROPE','CountryCode':'UK','ChannelName':'UK: COMEDY CENTRAL','EPGChannelID':'comedycentral.uk'}
        match,reason=g.safe_match(row,self.idx)
        self.assertEqual(match,('UK1','ComedyCentral.uk'))
        self.assertNotEqual(reason,'OBSERVED_UK_COMEDY_CENTRAL_FEED')

    def test_no_uk_source_leaves_wrong_us_guide_unassigned(self):
        idx=g.index_by_name({'US2':[('Comedy.Central.HD.us2',['Comedy Central HD'])]})
        match,reason=g.safe_match(self.us,idx)
        self.assertIsNone(match)
        self.assertEqual(reason,'UK_COMEDY_CENTRAL_SOURCE_UNAVAILABLE')

    def test_other_usa_channels_not_overridden(self):
        row=dict(self.us,ChannelName='USA: COMEDY CENTRAL EXTRA')
        match,reason=g.safe_match(row,self.idx)
        self.assertNotEqual(reason,'OBSERVED_UK_COMEDY_CENTRAL_FEED')

if __name__=='__main__':unittest.main()
