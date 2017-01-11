"""

  fs1.tests.test_wrapfs:  testcases for FS wrapper implementations

"""

import unittest
from fs1.tests import FSTestCases, ThreadingTestCases

import os
import sys
import shutil
import tempfile

from fs1 import osfs
from fs1.errors import *
from fs1.path import *
from fs1.utils import remove_all
from fs1 import wrapfs

import six
from six import PY3, b

class TestWrapFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    #__test__ = False

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.fs1 = wrapfs.WrapFS(osfs.OSFS(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.fs1.close()

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, relpath(p)))


from fs1.wrapfs.lazyfs import LazyFS
class TestLazyFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.fs1 = LazyFS((osfs.OSFS,(self.temp_dir,)))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.fs1.close()

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, relpath(p)))


from fs1.wrapfs.limitsizefs import LimitSizeFS
class TestLimitSizeFS(TestWrapFS):

    _dont_retest = TestWrapFS._dont_retest + ("test_big_file",)

    def setUp(self):
        super(TestLimitSizeFS,self).setUp()
        self.fs1 = LimitSizeFS(self.fs1,1024*1024*2)  # 2MB limit

    def tearDown(self):
        remove_all(self.fs1, "/")
        self.assertEquals(self.fs1.cur_size,0)
        super(TestLimitSizeFS,self).tearDown()
        self.fs1.close()

    def test_storage_error(self):
        total_written = 0
        for i in xrange(1024*2):
            try:
                total_written += 1030
                self.fs1.setcontents("file %i" % i, b("C")*1030)
            except StorageSpaceError:
                self.assertTrue(total_written > 1024*1024*2)
                self.assertTrue(total_written < 1024*1024*2 + 1030)
                break
        else:
            self.assertTrue(False,"StorageSpaceError not raised")


from fs1.wrapfs.hidedotfilesfs import HideDotFilesFS
class TestHideDotFilesFS(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        open(os.path.join(self.temp_dir, u".dotfile"), 'w').close()
        open(os.path.join(self.temp_dir, u"regularfile"), 'w').close()
        os.mkdir(os.path.join(self.temp_dir, u".dotdir"))
        os.mkdir(os.path.join(self.temp_dir, u"regulardir"))
        self.fs1 = HideDotFilesFS(osfs.OSFS(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.fs1.close()

    def test_hidden(self):
        self.assertEquals(len(self.fs1.listdir(hidden=False)), 2)
        self.assertEquals(len(list(self.fs1.ilistdir(hidden=False))), 2)

    def test_nonhidden(self):
        self.assertEquals(len(self.fs1.listdir(hidden=True)), 4)
        self.assertEquals(len(list(self.fs1.ilistdir(hidden=True))), 4)

    def test_default(self):
        self.assertEquals(len(self.fs1.listdir()), 2)
        self.assertEquals(len(list(self.fs1.ilistdir())), 2)


