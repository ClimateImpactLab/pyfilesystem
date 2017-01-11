"""

  fs1.tests.test_fs:  testcases for basic FS implementations

"""

from fs1.tests import FSTestCases, ThreadingTestCases
from fs1.path import *
from fs1 import errors

import unittest

import os
import sys
import shutil
import tempfile


from fs1 import osfs
class TestOSFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.fs1 = osfs.OSFS(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.fs1.close()

    def check(self, p):
        return os.path.exists(os.path.join(self.temp_dir, relpath(p)))

    def test_invalid_chars(self):
        super(TestOSFS, self).test_invalid_chars()

        self.assertRaises(errors.InvalidCharsInPathError, self.fs1.open, 'invalid\0file', 'wb')
        self.assertFalse(self.fs1.isvalidpath('invalid\0file'))
        self.assert_(self.fs1.isvalidpath('validfile'))
        self.assert_(self.fs1.isvalidpath('completely_valid/path/foo.bar'))


class TestSubFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(u"fstest")
        self.parent_fs = osfs.OSFS(self.temp_dir)
        self.parent_fs.makedir("foo/bar", recursive=True)
        self.fs1 = self.parent_fs.opendir("foo/bar")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.fs1.close()

    def check(self, p):
        p = os.path.join("foo/bar", relpath(p))
        full_p = os.path.join(self.temp_dir, p)
        return os.path.exists(full_p)


from fs1 import memoryfs
class TestMemoryFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.fs1 = memoryfs.MemoryFS()


from fs1 import mountfs
class TestMountFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.mount_fs = mountfs.MountFS()
        self.mem_fs = memoryfs.MemoryFS()
        self.mount_fs.mountdir("mounted/memfs", self.mem_fs)
        self.fs1 = self.mount_fs.opendir("mounted/memfs")

    def tearDown(self):
        self.fs1.close()

    def check(self, p):
        return self.mount_fs.exists(pathjoin("mounted/memfs", relpath(p)))

class TestMountFS_atroot(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.mem_fs = memoryfs.MemoryFS()
        self.fs1 = mountfs.MountFS()
        self.fs1.mountdir("", self.mem_fs)

    def tearDown(self):
        self.fs1.close()

    def check(self, p):
        return self.mem_fs.exists(p)

class TestMountFS_stacked(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.mem_fs1 = memoryfs.MemoryFS()
        self.mem_fs2 = memoryfs.MemoryFS()
        self.mount_fs = mountfs.MountFS()
        self.mount_fs.mountdir("mem", self.mem_fs1)
        self.mount_fs.mountdir("mem/two", self.mem_fs2)
        self.fs1 = self.mount_fs.opendir("/mem/two")

    def tearDown(self):
        self.fs1.close()

    def check(self, p):
        return self.mount_fs.exists(pathjoin("mem/two", relpath(p)))


from fs1 import tempfs
class TestTempFS(unittest.TestCase,FSTestCases,ThreadingTestCases):

    def setUp(self):
        self.fs1 = tempfs.TempFS()

    def tearDown(self):
        td = self.fs1._temp_dir
        self.fs1.close()
        self.assert_(not os.path.exists(td))

    def check(self, p):
        td = self.fs1._temp_dir
        return os.path.exists(os.path.join(td, relpath(p)))

    def test_invalid_chars(self):
        super(TestTempFS, self).test_invalid_chars()

        self.assertRaises(errors.InvalidCharsInPathError, self.fs1.open, 'invalid\0file', 'wb')
        self.assertFalse(self.fs1.isvalidpath('invalid\0file'))
        self.assert_(self.fs1.isvalidpath('validfile'))
        self.assert_(self.fs1.isvalidpath('completely_valid/path/foo.bar'))
