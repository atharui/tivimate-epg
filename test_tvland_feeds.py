"""TV Land country-feed identity and explicit alternative guides."""
import unittest
from collections import defaultdict
from build_custom_epg import add_tv_land_choices

class TVLandTests(unittest.TestCase):
    @staticmethod
    def guides():
        return defaultdict(lambda:defaultdict(set)), defaultdict(list)

    def test_east_and_pacific_choices_never_auto_use_generic_name(self):
        rows=[{'Region':'USA','ChannelName':'USA: TV LAND HD'}]
        catalog={'US2':[('TV.Land.HD.us2',['TV Land HD']),
                        ('TV.Land.HD.(Pacific).us2',['TV Land HD Pacific'])]}
        matched,names=self.guides()
        count=add_tv_land_choices(rows,catalog,matched,names)
        self.assertEqual(count,2)
        self.assertEqual(matched['US2']['TV.Land.HD.us2'], {'TV.Land.HD.us2'})
        self.assertEqual(matched['US2']['TV.Land.HD.(Pacific).us2'], {'TV.Land.HD.(Pacific).us2'})
        self.assertTrue(any('EASTERN' in x for x in names['TV.Land.HD.us2']))
        self.assertTrue(any('PACIFIC' in x for x in names['TV.Land.HD.(Pacific).us2']))
        self.assertNotIn('USA: TV LAND HD',sum(names.values(), []))

    def test_missing_pacific_does_not_make_up_western_guide(self):
        rows=[{'Region':'USA','ChannelName':'USA: TV LAND HD'}]
        matched,names=self.guides()
        count=add_tv_land_choices(rows,{'US2':[('TV.Land.HD.us2',[])]},matched,names)
        self.assertEqual(count,1)
        self.assertNotIn('TV.Land.HD.(Pacific).us2',names)

    def test_no_tvland_playlist_entry_means_no_manual_options(self):
        rows=[{'Region':'USA','ChannelName':'USA: USA NETWORK'}]
        matched,names=self.guides()
        count=add_tv_land_choices(rows,{'US2':[('TV.Land.HD.us2',[])]},matched,names)
        self.assertEqual(count,0)
        self.assertFalse(names)

if __name__=='__main__':
    unittest.main()
