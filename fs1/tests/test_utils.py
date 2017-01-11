import unittest

from fs1.tempfs import TempFS
from fs1.memoryfs import MemoryFS
from fs1 import utils

from six import b

class TestUtils(unittest.TestCase):

    def _make_fs(self, fs1):
        fs1.setcontents("f1", b("file 1"))
        fs1.setcontents("f2", b("file 2"))
        fs1.setcontents("f3", b("file 3"))
        fs1.makedir("foo/bar", recursive=True)
        fs1.setcontents("foo/bar/fruit", b("apple"))

    def _check_fs(self, fs1):
        self.assert_(fs1.isfile("f1"))
        self.assert_(fs1.isfile("f2"))
        self.assert_(fs1.isfile("f3"))
        self.assert_(fs1.isdir("foo/bar"))
        self.assert_(fs1.isfile("foo/bar/fruit"))
        self.assertEqual(fs1.getcontents("f1", "rb"), b("file 1"))
        self.assertEqual(fs1.getcontents("f2", "rb"), b("file 2"))
        self.assertEqual(fs1.getcontents("f3", "rb"), b("file 3"))
        self.assertEqual(fs1.getcontents("foo/bar/fruit", "rb"), b("apple"))

    def test_copydir_root(self):
        """Test copydir from root"""
        fs1 = MemoryFS()
        self._make_fs(fs1)
        fs2 = MemoryFS()
        utils.copydir(fs1, fs2)
        self._check_fs(fs2)

        fs1 = TempFS()
        self._make_fs(fs1)
        fs2 = TempFS()
        utils.copydir(fs1, fs2)
        self._check_fs(fs2)

    def test_copydir_indir(self):
        """Test copydir in a directory"""
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        self._make_fs(fs1)
        utils.copydir(fs1, (fs2, "copy"))
        self._check_fs(fs2.opendir("copy"))

        fs1 = TempFS()
        fs2 = TempFS()
        self._make_fs(fs1)
        utils.copydir(fs1, (fs2, "copy"))
        self._check_fs(fs2.opendir("copy"))

    def test_movedir_indir(self):
        """Test movedir in a directory"""
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)
        utils.movedir((fs1, "from"), (fs2, "copy"))
        self.assert_(not fs1.exists("from"))
        self._check_fs(fs2.opendir("copy"))

        fs1 = TempFS()
        fs2 = TempFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)
        utils.movedir((fs1, "from"), (fs2, "copy"))
        self.assert_(not fs1.exists("from"))
        self._check_fs(fs2.opendir("copy"))

    def test_movedir_root(self):
        """Test movedir to root dir"""
        fs1 = MemoryFS()
        fs2 = MemoryFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)
        utils.movedir((fs1, "from"), fs2)
        self.assert_(not fs1.exists("from"))
        self._check_fs(fs2)

        fs1 = TempFS()
        fs2 = TempFS()
        fs1sub = fs1.makeopendir("from")
        self._make_fs(fs1sub)
        utils.movedir((fs1, "from"), fs2)
        self.assert_(not fs1.exists("from"))
        self._check_fs(fs2)

    def test_remove_all(self):
        """Test remove_all function"""
        fs1 = TempFS()
        fs1.setcontents("f1", b("file 1"))
        fs1.setcontents("f2", b("file 2"))
        fs1.setcontents("f3", b("file 3"))
        fs1.makedir("foo/bar", recursive=True)
        fs1.setcontents("foo/bar/fruit", b("apple"))
        fs1.setcontents("foo/baz", b("baz"))

        utils.remove_all(fs1, "foo/bar")
        self.assert_(not fs1.exists("foo/bar/fruit"))
        self.assert_(fs1.exists("foo/bar"))
        self.assert_(fs1.exists("foo/baz"))
        utils.remove_all(fs1,  "")
        self.assert_(not fs1.exists("foo/bar/fruit"))
        self.assert_(not fs1.exists("foo/bar/baz"))
        self.assert_(not fs1.exists("foo/baz"))
        self.assert_(not fs1.exists("foo"))
        self.assert_(not fs1.exists("f1"))
        self.assert_(fs1.isdirempty('/'))


