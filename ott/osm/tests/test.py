import os
import unittest

from ott.osm.rename.osm_rename import OsmRename
from ott.utils import file_utils


class TestOsmRename(unittest.TestCase):

    def setUp(self):
        self.thisdir = file_utils.get_module_dir(self.__class__)
        self.full_names_regexp = "North|South|East|West|Street|Avenue|Terrace|Road"

    def tearDown(self):
        pass

    def test_rename(self):
        osm_in = os.path.join(self.thisdir, "data", "test_data.osm")
        osm_out = os.path.join(self.thisdir, "data", "test_renamed.osm")
        OsmRename.rename(osm_in, osm_out)
        r = file_utils.grep(osm_out, self.full_names_regexp)
        self.assertTrue(len(r) == 0)

    def test_utf8_renames(self):
        osm_in = os.path.join(self.thisdir, "data", "test_data_utf8.osm")
        osm_out = os.path.join(self.thisdir, "data", "test_utf8_renamed.osm")
        OsmRename.rename(osm_in, osm_out)
        r = file_utils.grep(osm_out, self.full_names_regexp)
        self.assertTrue(len(r) == 0)

    def test_no_process_after_rename_tag(self):
        """ the renamer should not engage when the generator attribute is marked as previously renamed in the <osm> tag
            <osm version="0.6" generator="Osmosis 0.45; streets renamed by OpenTransitTools">
        """
        osm_in = os.path.join(self.thisdir, "data", "test_dont_rename_again.osm")
        osm_out = os.path.join(self.thisdir, "data", "test_not_renamed.osm")
        OsmRename.rename(osm_in, osm_out)
        r = file_utils.grep(osm_out, self.full_names_regexp)
        self.assertTrue(len(r) > 0)  # note: expect to grep multiple full names, since the renamer should not engage

    def test_problematic_strings(self):
        osm_in = os.path.join(self.thisdir, "data", "test_data_problematic_strings.osm")
        osm_out = os.path.join(self.thisdir, "data", "test_renamed_problematic_strings.osm")
        OsmRename.rename(osm_in, osm_out)

        # !!!!!!!!!!!! IMPORTANT - this test currently fails (as of 2018) !!!!!!!!!!!!

        # note: these strings currently not working -- @see:
        #   bin/osm_rename ott/loader/osm/rename/tests/test_data_problematic_strings.osm x; cat x
        problem_strs = ['=&gt;', '/', '|', '^', '%', '*', '&amp;', '=&gt;/|^%**&amp;']
        for p in problem_strs:
            r = file_utils.grep(osm_out, u"A{}B".format(p))
            self.assertTrue(len(r) == 1)

            r = file_utils.grep(osm_out, u"SE {} Rd".format(p))
            self.assertTrue(len(r) == 1)

            r = file_utils.grep(osm_out, u"NW {}Street".format(p))
            self.assertTrue(len(r) == 1)


class TestOsmIntersections(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_diff_calendar(self):
        # import pdb; pdb.set_trace()
        #self.assertTrue()
        pass

