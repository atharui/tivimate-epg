"""TV Land east/west guide regression tests (no subscription needed)."""
import unittest
from collections import defaultdict
from build_custom_epg import add_tv_land_pacific_option

class TVLandTests(unittest.TestCase):
    def setup_guides(self):
        return defaultdict(lambda: defaultdict(set)), defaultdict(list)

    def test_both_feeds_can_be_available_without_overwriting_east(self):
        rows=[{'Region':'USA','ChannelName':'USA: TV LAND HD'}]
        catalog={'US2':[('TV.Land.HD.us2',['TV Land HD']),('TV.Land.HD.(Pacific).us2',['TV Land HD Pacific'])]}
        matched,names=self.setup_guides()
        matched['US2']['TV.Land.HD.us2'].add('TV.Land.HD.us2')
        names['TV.Land.HD.us2']=['USA: TV LAND HD']
        self.assertTrue(add_tv_land_pacific_option(rows,catalog,matched,names))
        self.assertEqual(matched['US2']['TV.Land.HD.us2'], {'TV.Land.HD.us2'})
        self.assertEqual(matched['US2']['TV.Land.HD.(Pacific).us2'], {'TV.Land.HD.(Pacific).us2'})
        self.assertIn('TV LAND WEST',names['TV.Land.HD.(Pacific).us2'])

    def test_do_not_invent_missing_pacific_epg(self):
        rows=[{'Region':'USA','ChannelName':'USA: TV LAND HD'}]
        matched,names=self.setup_guides()
        self.assertFalse(add_tv_land_pacific_option(rows,{'US2':[('TV.Land.HD.us2',[])]},matched,names))
        self.assertFalse(names)

    def test_do_not_insert_tv_land_when_not_in_playlist(self):
        rows=[{'Region':'USA','ChannelName':'USA: USA NETWORK'}]
        matched,names=self.setup_guides()
        self.assertFalse(add_tv_land_pacific_option(rows,{'US2':[('TV.Land.HD.(Pacific).us2',[])]},matched,names))

if __name__=='__main__':
    unittest.main()
