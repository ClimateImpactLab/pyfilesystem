"""

  fs1.tests.test_xattr:  testcases for extended attribute support

"""

import unittest
import os

from fs1.path import *
from fs1.errors import *
from fs1.tests import FSTestCases

from six import b

class XAttrTestCases:
    """Testcases for filesystems providing extended attribute support.

    This class should be used as a mixin to the unittest.TestCase class
    for filesystems that provide extended attribute support.
    """

    def test_getsetdel(self):
        def do_getsetdel(p):
            self.assertEqual(self.fs1.getxattr(p,"xattr1"),None)
            self.fs1.setxattr(p,"xattr1","value1")
            self.assertEqual(self.fs1.getxattr(p,"xattr1"),"value1")
            self.fs1.delxattr(p,"xattr1")
            self.assertEqual(self.fs1.getxattr(p,"xattr1"),None)
        self.fs1.setcontents("test.txt",b("hello"))
        do_getsetdel("test.txt")
        self.assertRaises(ResourceNotFoundError,self.fs1.getxattr,"test2.txt","xattr1")
        self.fs1.makedir("mystuff")
        self.fs1.setcontents("/mystuff/test.txt",b(""))
        do_getsetdel("mystuff")
        do_getsetdel("mystuff/test.txt")

    def test_list_xattrs(self):
        def do_list(p):
            self.assertEquals(sorted(self.fs1.listxattrs(p)),[])
            self.fs1.setxattr(p,"xattr1","value1")
            self.assertEquals(self.fs1.getxattr(p,"xattr1"),"value1")
            self.assertEquals(sorted(self.fs1.listxattrs(p)),["xattr1"])
            self.assertTrue(isinstance(self.fs1.listxattrs(p)[0],unicode))
            self.fs1.setxattr(p,"attr2","value2")
            self.assertEquals(sorted(self.fs1.listxattrs(p)),["attr2","xattr1"])
            self.assertTrue(isinstance(self.fs1.listxattrs(p)[0],unicode))
            self.assertTrue(isinstance(self.fs1.listxattrs(p)[1],unicode))
            self.fs1.delxattr(p,"xattr1")
            self.assertEquals(sorted(self.fs1.listxattrs(p)),["attr2"])
            self.fs1.delxattr(p,"attr2")
            self.assertEquals(sorted(self.fs1.listxattrs(p)),[])
        self.fs1.setcontents("test.txt",b("hello"))
        do_list("test.txt")
        self.fs1.makedir("mystuff")
        self.fs1.setcontents("/mystuff/test.txt",b(""))
        do_list("mystuff")
        do_list("mystuff/test.txt")

    def test_copy_xattrs(self):
        self.fs1.setcontents("a.txt",b("content"))
        self.fs1.setxattr("a.txt","myattr","myvalue")
        self.fs1.setxattr("a.txt","testattr","testvalue")
        self.fs1.makedir("stuff")
        self.fs1.copy("a.txt","stuff/a.txt")
        self.assertTrue(self.fs1.exists("stuff/a.txt"))
        self.assertEquals(self.fs1.getxattr("stuff/a.txt","myattr"),"myvalue")
        self.assertEquals(self.fs1.getxattr("stuff/a.txt","testattr"),"testvalue")
        self.assertEquals(self.fs1.getxattr("a.txt","myattr"),"myvalue")
        self.assertEquals(self.fs1.getxattr("a.txt","testattr"),"testvalue")
        self.fs1.setxattr("stuff","dirattr","a directory")
        self.fs1.copydir("stuff","stuff2")
        self.assertEquals(self.fs1.getxattr("stuff2/a.txt","myattr"),"myvalue")
        self.assertEquals(self.fs1.getxattr("stuff2/a.txt","testattr"),"testvalue")
        self.assertEquals(self.fs1.getxattr("stuff2","dirattr"),"a directory")
        self.assertEquals(self.fs1.getxattr("stuff","dirattr"),"a directory")

    def test_move_xattrs(self):
        self.fs1.setcontents("a.txt",b("content"))
        self.fs1.setxattr("a.txt","myattr","myvalue")
        self.fs1.setxattr("a.txt","testattr","testvalue")
        self.fs1.makedir("stuff")
        self.fs1.move("a.txt","stuff/a.txt")
        self.assertTrue(self.fs1.exists("stuff/a.txt"))
        self.assertEquals(self.fs1.getxattr("stuff/a.txt","myattr"),"myvalue")
        self.assertEquals(self.fs1.getxattr("stuff/a.txt","testattr"),"testvalue")
        self.fs1.setxattr("stuff","dirattr","a directory")
        self.fs1.movedir("stuff","stuff2")
        self.assertEquals(self.fs1.getxattr("stuff2/a.txt","myattr"),"myvalue")
        self.assertEquals(self.fs1.getxattr("stuff2/a.txt","testattr"),"testvalue")
        self.assertEquals(self.fs1.getxattr("stuff2","dirattr"),"a directory")

    def test_remove_file(self):
        def listxattrs(path):
            return list(self.fs1.listxattrs(path))
        #  Check that xattrs aren't preserved after a file is removed
        self.fs1.createfile("myfile")
        self.assertEquals(listxattrs("myfile"),[])
        self.fs1.setxattr("myfile","testattr","testvalue")
        self.assertEquals(listxattrs("myfile"),["testattr"])
        self.fs1.remove("myfile")
        self.assertRaises(ResourceNotFoundError,listxattrs,"myfile")
        self.fs1.createfile("myfile")
        self.assertEquals(listxattrs("myfile"),[])
        self.fs1.setxattr("myfile","testattr2","testvalue2")
        self.assertEquals(listxattrs("myfile"),["testattr2"])
        self.assertEquals(self.fs1.getxattr("myfile","testattr2"),"testvalue2")
        #  Check that removing a file without xattrs still works
        self.fs1.createfile("myfile2")
        self.fs1.remove("myfile2")

    def test_remove_dir(self):
        def listxattrs(path):
            return list(self.fs1.listxattrs(path))
        #  Check that xattrs aren't preserved after a dir is removed
        self.fs1.makedir("mydir")
        self.assertEquals(listxattrs("mydir"),[])
        self.fs1.setxattr("mydir","testattr","testvalue")
        self.assertEquals(listxattrs("mydir"),["testattr"])
        self.fs1.removedir("mydir")
        self.assertRaises(ResourceNotFoundError,listxattrs,"mydir")
        self.fs1.makedir("mydir")
        self.assertEquals(listxattrs("mydir"),[])
        self.fs1.setxattr("mydir","testattr2","testvalue2")
        self.assertEquals(listxattrs("mydir"),["testattr2"])
        self.assertEquals(self.fs1.getxattr("mydir","testattr2"),"testvalue2")
        #  Check that removing a dir without xattrs still works
        self.fs1.makedir("mydir2")
        self.fs1.removedir("mydir2")
        #  Check that forcibly removing a dir with xattrs still works
        self.fs1.makedir("mydir3")
        self.fs1.createfile("mydir3/testfile")
        self.fs1.removedir("mydir3",force=True)
        self.assertFalse(self.fs1.exists("mydir3"))


from fs1.xattrs import ensure_xattrs

from fs1 import tempfs
class TestXAttr_TempFS(unittest.TestCase,FSTestCases,XAttrTestCases):

    def setUp(self):
        fs1 = tempfs.TempFS()
        self.fs1 = ensure_xattrs(fs1)

    def tearDown(self):
        try:
            td = self.fs1._temp_dir
        except AttributeError:
            td = self.fs1.wrapped_fs._temp_dir
        self.fs1.close()
        self.assert_(not os.path.exists(td))

    def check(self, p):
        try:
            td = self.fs1._temp_dir
        except AttributeError:
            td = self.fs1.wrapped_fs._temp_dir
        return os.path.exists(os.path.join(td, relpath(p)))


from fs1 import memoryfs
class TestXAttr_MemoryFS(unittest.TestCase,FSTestCases,XAttrTestCases):

    def setUp(self):
        self.fs1 = ensure_xattrs(memoryfs.MemoryFS())

    def check(self, p):
        return self.fs1.exists(p)


