#!/usr/bin/python
"""
    Test the TahoeLAFS

    @author: Marek Palatinus <marek@palatinus.cz>
"""

import sys
import logging
import unittest

from fs1.base import FS
import fs1.errors as errors
from fs1.tests import FSTestCases, ThreadingTestCases
from fs1.contrib.tahoelafs import TahoeLAFS, Connection

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('fs1.tahoelafs').addHandler(logging.StreamHandler(sys.stdout))

WEBAPI = 'http://insecure.tahoe-lafs.org'


#  The public grid is too slow for threading testcases, disabling for now...
class TestTahoeLAFS(unittest.TestCase,FSTestCases):#,ThreadingTestCases):

    #  Disabled by default because it takes a *really* long time.
    __test__ = False

    def setUp(self):
        self.dircap = TahoeLAFS.createdircap(WEBAPI)
        self.fs1 = TahoeLAFS(self.dircap, cache_timeout=0, webapi=WEBAPI)

    def tearDown(self):
        self.fs1.close()

    def test_dircap(self):
        # Is dircap in correct format?
        self.assert_(self.dircap.startswith('URI:DIR2:') and len(self.dircap) > 50)

    def test_concurrent_copydir(self):
        #  makedir() on TahoeLAFS is currently not atomic
        pass

    def test_makedir_winner(self):
        #  makedir() on TahoeLAFS is currently not atomic
        pass

    def test_big_file(self):
        pass

if __name__ == '__main__':
    unittest.main()
