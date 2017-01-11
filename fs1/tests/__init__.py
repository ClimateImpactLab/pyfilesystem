#!/usr/bin/env python
"""

  fs1.tests:  testcases for the fs1 module

"""

from __future__ import with_statement

#  Send any output from the logging module to stdout, so it will
#  be captured by nose and reported appropriately
import sys
import logging
logging.basicConfig(level=logging.ERROR, stream=sys.stdout)

from fs1.base import *
from fs1.path import *
from fs1.errors import *
from fs1.filelike import StringIO

import datetime
import unittest
import os
import os.path
import pickle
import random
import copy

import time
try:
    import threading
except ImportError:
    import dummy_threading as threading

import six
from six import PY3, b


class FSTestCases(object):
    """Base suite of testcases for filesystem implementations.

    Any FS subclass should be capable of passing all of these tests.
    To apply the tests to your own FS implementation, simply use FSTestCase
    as a mixin for your own unittest.TestCase subclass and have the setUp
    method set self.fs1 to an instance of your FS implementation.

    NB. The Filesystem being tested must have a capacity of at least 3MB.

    This class is designed as a mixin so that it's not detected by test
    loading tools such as nose.
    """

    def check(self, p):
        """Check that a file exists within self.fs1"""
        return self.fs1.exists(p)

    def test_invalid_chars(self):
        """Check paths validate ok"""
        # Will have to be overriden selectively for custom validepath methods
        self.assertEqual(self.fs1.validatepath(''), None)
        self.assertEqual(self.fs1.validatepath('.foo'), None)
        self.assertEqual(self.fs1.validatepath('foo'), None)
        self.assertEqual(self.fs1.validatepath('foo/bar'), None)
        self.assert_(self.fs1.isvalidpath('foo/bar'))

    def test_tree(self):
        """Test tree print"""
        self.fs1.makedir('foo')
        self.fs1.createfile('foo/bar.txt')
        self.fs1.tree()

    def test_meta(self):
        """Checks getmeta / hasmeta are functioning"""
        # getmeta / hasmeta are hard to test, since there is no way to validate
        # the implementation's response
        meta_names = ["read_only",
                      "network",
                      "unicode_paths"]
        stupid_meta = 'thismetashouldnotexist!"r$$%^&&*()_+'
        self.assertRaises(NoMetaError, self.fs1.getmeta, stupid_meta)
        self.assertFalse(self.fs1.hasmeta(stupid_meta))
        self.assertEquals(None, self.fs1.getmeta(stupid_meta, None))
        self.assertEquals(3.14, self.fs1.getmeta(stupid_meta, 3.14))
        for meta_name in meta_names:
            try:
                meta = self.fs1.getmeta(meta_name)
                self.assertTrue(self.fs1.hasmeta(meta_name))
            except NoMetaError:
                self.assertFalse(self.fs1.hasmeta(meta_name))

    def test_root_dir(self):
        self.assertTrue(self.fs1.isdir(""))
        self.assertTrue(self.fs1.isdir("/"))
        # These may be false (e.g. empty dict) but mustn't raise errors
        self.fs1.getinfo("")
        self.assertTrue(self.fs1.getinfo("/") is not None)

    def test_getsyspath(self):
        try:
            syspath = self.fs1.getsyspath("/")
        except NoSysPathError:
            pass
        else:
            self.assertTrue(isinstance(syspath, unicode))
        syspath = self.fs1.getsyspath("/", allow_none=True)
        if syspath is not None:
            self.assertTrue(isinstance(syspath, unicode))

    def test_debug(self):
        str(self.fs1)
        repr(self.fs1)
        self.assert_(hasattr(self.fs1, 'desc'))

    def test_open_on_directory(self):
        self.fs1.makedir("testdir")
        try:
            f = self.fs1.open("testdir")
        except ResourceInvalidError:
            pass
        except Exception:
            raise
            ecls = sys.exc_info()[0]
            assert False, "%s raised instead of ResourceInvalidError" % (ecls,)
        else:
            f.close()
            assert False, "ResourceInvalidError was not raised"

    def test_writefile(self):
        self.assertRaises(ResourceNotFoundError, self.fs1.open, "test1.txt")
        f = self.fs1.open("test1.txt", "wb")
        f.write(b("testing"))
        f.close()
        self.assertTrue(self.check("test1.txt"))
        f = self.fs1.open("test1.txt", "rb")
        self.assertEquals(f.read(), b("testing"))
        f.close()
        f = self.fs1.open("test1.txt", "wb")
        f.write(b("test file overwrite"))
        f.close()
        self.assertTrue(self.check("test1.txt"))
        f = self.fs1.open("test1.txt", "rb")
        self.assertEquals(f.read(), b("test file overwrite"))
        f.close()

    def test_createfile(self):
        test = b('now with content')
        self.fs1.createfile("test.txt")
        self.assert_(self.fs1.exists("test.txt"))
        self.assertEqual(self.fs1.getcontents("test.txt", "rb"), b(''))
        self.fs1.setcontents("test.txt", test)
        self.fs1.createfile("test.txt")
        self.assertEqual(self.fs1.getcontents("test.txt", "rb"), test)
        self.fs1.createfile("test.txt", wipe=True)
        self.assertEqual(self.fs1.getcontents("test.txt", "rb"), b(''))

    def test_readline(self):
        text = b"Hello\nWorld\n"
        self.fs1.setcontents('a.txt', text)
        with self.fs1.open('a.txt', 'rb') as f:
            line = f.readline()
        self.assertEqual(line, b"Hello\n")

    def test_setcontents(self):
        #  setcontents() should accept both a string...
        self.fs1.setcontents("hello", b("world"))
        self.assertEquals(self.fs1.getcontents("hello", "rb"), b("world"))
        #  ...and a file-like object
        self.fs1.setcontents("hello", StringIO(b("to you, good sir!")))
        self.assertEquals(self.fs1.getcontents(
            "hello", "rb"), b("to you, good sir!"))
        #  setcontents() should accept both a string...
        self.fs1.setcontents("hello", b("world"), chunk_size=2)
        self.assertEquals(self.fs1.getcontents("hello", "rb"), b("world"))
        #  ...and a file-like object
        self.fs1.setcontents("hello", StringIO(
            b("to you, good sir!")), chunk_size=2)
        self.assertEquals(self.fs1.getcontents(
            "hello", "rb"), b("to you, good sir!"))
        self.fs1.setcontents("hello", b(""))
        self.assertEquals(self.fs1.getcontents("hello", "rb"), b(""))

    def test_setcontents_async(self):
        #  setcontents() should accept both a string...
        self.fs1.setcontents_async("hello", b("world")).wait()
        self.assertEquals(self.fs1.getcontents("hello", "rb"), b("world"))
        #  ...and a file-like object
        self.fs1.setcontents_async("hello", StringIO(
            b("to you, good sir!"))).wait()
        self.assertEquals(self.fs1.getcontents("hello"), b("to you, good sir!"))
        self.fs1.setcontents_async("hello", b("world"), chunk_size=2).wait()
        self.assertEquals(self.fs1.getcontents("hello", "rb"), b("world"))
        #  ...and a file-like object
        self.fs1.setcontents_async("hello", StringIO(
            b("to you, good sir!")), chunk_size=2).wait()
        self.assertEquals(self.fs1.getcontents(
            "hello", "rb"), b("to you, good sir!"))

    def test_isdir_isfile(self):
        self.assertFalse(self.fs1.exists("dir1"))
        self.assertFalse(self.fs1.isdir("dir1"))
        self.assertFalse(self.fs1.isfile("a.txt"))
        self.fs1.setcontents("a.txt", b(''))
        self.assertFalse(self.fs1.isdir("dir1"))
        self.assertTrue(self.fs1.exists("a.txt"))
        self.assertTrue(self.fs1.isfile("a.txt"))
        self.assertFalse(self.fs1.exists("a.txt/thatsnotadir"))
        self.fs1.makedir("dir1")
        self.assertTrue(self.fs1.isdir("dir1"))
        self.assertTrue(self.fs1.exists("dir1"))
        self.assertTrue(self.fs1.exists("a.txt"))
        self.fs1.remove("a.txt")
        self.assertFalse(self.fs1.exists("a.txt"))

    def test_listdir(self):
        def check_unicode(items):
            for item in items:
                self.assertTrue(isinstance(item, unicode))
        self.fs1.setcontents(u"a", b(''))
        self.fs1.setcontents("b", b(''))
        self.fs1.setcontents("foo", b(''))
        self.fs1.setcontents("bar", b(''))
        # Test listing of the root directory
        d1 = self.fs1.listdir()
        self.assertEqual(len(d1), 4)
        self.assertEqual(sorted(d1), [u"a", u"b", u"bar", u"foo"])
        check_unicode(d1)
        d1 = self.fs1.listdir("")
        self.assertEqual(len(d1), 4)
        self.assertEqual(sorted(d1), [u"a", u"b", u"bar", u"foo"])
        check_unicode(d1)
        d1 = self.fs1.listdir("/")
        self.assertEqual(len(d1), 4)
        check_unicode(d1)
        # Test listing absolute paths
        d2 = self.fs1.listdir(absolute=True)
        self.assertEqual(len(d2), 4)
        self.assertEqual(sorted(d2), [u"/a", u"/b", u"/bar", u"/foo"])
        check_unicode(d2)
        # Create some deeper subdirectories, to make sure their
        # contents are not inadvertantly included
        self.fs1.makedir("p/1/2/3", recursive=True)
        self.fs1.setcontents("p/1/2/3/a", b(''))
        self.fs1.setcontents("p/1/2/3/b", b(''))
        self.fs1.setcontents("p/1/2/3/foo", b(''))
        self.fs1.setcontents("p/1/2/3/bar", b(''))
        self.fs1.makedir("q")
        # Test listing just files, just dirs, and wildcards
        dirs_only = self.fs1.listdir(dirs_only=True)
        files_only = self.fs1.listdir(files_only=True)
        contains_a = self.fs1.listdir(wildcard="*a*")
        self.assertEqual(sorted(dirs_only), [u"p", u"q"])
        self.assertEqual(sorted(files_only), [u"a", u"b", u"bar", u"foo"])
        self.assertEqual(sorted(contains_a), [u"a", u"bar"])
        check_unicode(dirs_only)
        check_unicode(files_only)
        check_unicode(contains_a)
        # Test listing a subdirectory
        d3 = self.fs1.listdir("p/1/2/3")
        self.assertEqual(len(d3), 4)
        self.assertEqual(sorted(d3), [u"a", u"b", u"bar", u"foo"])
        check_unicode(d3)
        # Test listing a subdirectory with absoliute and full paths
        d4 = self.fs1.listdir("p/1/2/3", absolute=True)
        self.assertEqual(len(d4), 4)
        self.assertEqual(sorted(d4), [u"/p/1/2/3/a", u"/p/1/2/3/b", u"/p/1/2/3/bar", u"/p/1/2/3/foo"])
        check_unicode(d4)
        d4 = self.fs1.listdir("p/1/2/3", full=True)
        self.assertEqual(len(d4), 4)
        self.assertEqual(sorted(d4), [u"p/1/2/3/a", u"p/1/2/3/b", u"p/1/2/3/bar", u"p/1/2/3/foo"])
        check_unicode(d4)
        # Test that appropriate errors are raised
        self.assertRaises(ResourceNotFoundError, self.fs1.listdir, "zebra")
        self.assertRaises(ResourceInvalidError, self.fs1.listdir, "foo")

    def test_listdirinfo(self):
        def check_unicode(items):
            for (nm, info) in items:
                self.assertTrue(isinstance(nm, unicode))

        def check_equal(items, target):
            names = [nm for (nm, info) in items]
            self.assertEqual(sorted(names), sorted(target))
        self.fs1.setcontents(u"a", b(''))
        self.fs1.setcontents("b", b(''))
        self.fs1.setcontents("foo", b(''))
        self.fs1.setcontents("bar", b(''))
        # Test listing of the root directory
        d1 = self.fs1.listdirinfo()
        self.assertEqual(len(d1), 4)
        check_equal(d1, [u"a", u"b", u"bar", u"foo"])
        check_unicode(d1)
        d1 = self.fs1.listdirinfo("")
        self.assertEqual(len(d1), 4)
        check_equal(d1, [u"a", u"b", u"bar", u"foo"])
        check_unicode(d1)
        d1 = self.fs1.listdirinfo("/")
        self.assertEqual(len(d1), 4)
        check_equal(d1, [u"a", u"b", u"bar", u"foo"])
        check_unicode(d1)
        # Test listing absolute paths
        d2 = self.fs1.listdirinfo(absolute=True)
        self.assertEqual(len(d2), 4)
        check_equal(d2, [u"/a", u"/b", u"/bar", u"/foo"])
        check_unicode(d2)
        # Create some deeper subdirectories, to make sure their
        # contents are not inadvertantly included
        self.fs1.makedir("p/1/2/3", recursive=True)
        self.fs1.setcontents("p/1/2/3/a", b(''))
        self.fs1.setcontents("p/1/2/3/b", b(''))
        self.fs1.setcontents("p/1/2/3/foo", b(''))
        self.fs1.setcontents("p/1/2/3/bar", b(''))
        self.fs1.makedir("q")
        # Test listing just files, just dirs, and wildcards
        dirs_only = self.fs1.listdirinfo(dirs_only=True)
        files_only = self.fs1.listdirinfo(files_only=True)
        contains_a = self.fs1.listdirinfo(wildcard="*a*")
        check_equal(dirs_only, [u"p", u"q"])
        check_equal(files_only, [u"a", u"b", u"bar", u"foo"])
        check_equal(contains_a, [u"a", u"bar"])
        check_unicode(dirs_only)
        check_unicode(files_only)
        check_unicode(contains_a)
        # Test listing a subdirectory
        d3 = self.fs1.listdirinfo("p/1/2/3")
        self.assertEqual(len(d3), 4)
        check_equal(d3, [u"a", u"b", u"bar", u"foo"])
        check_unicode(d3)
        # Test listing a subdirectory with absoliute and full paths
        d4 = self.fs1.listdirinfo("p/1/2/3", absolute=True)
        self.assertEqual(len(d4), 4)
        check_equal(d4, [u"/p/1/2/3/a", u"/p/1/2/3/b", u"/p/1/2/3/bar", u"/p/1/2/3/foo"])
        check_unicode(d4)
        d4 = self.fs1.listdirinfo("p/1/2/3", full=True)
        self.assertEqual(len(d4), 4)
        check_equal(d4, [u"p/1/2/3/a", u"p/1/2/3/b", u"p/1/2/3/bar", u"p/1/2/3/foo"])
        check_unicode(d4)
        # Test that appropriate errors are raised
        self.assertRaises(ResourceNotFoundError, self.fs1.listdirinfo, "zebra")
        self.assertRaises(ResourceInvalidError, self.fs1.listdirinfo, "foo")

    def test_walk(self):
        self.fs1.setcontents('a.txt', b('hello'))
        self.fs1.setcontents('b.txt', b('world'))
        self.fs1.makeopendir('foo').setcontents('c', b('123'))
        sorted_walk = sorted([(d, sorted(fs1)) for (d, fs1) in self.fs1.walk()])
        self.assertEquals(sorted_walk,
                          [("/", ["a.txt", "b.txt"]),
                           ("/foo", ["c"])])
        #  When searching breadth-first, shallow entries come first
        found_a = False
        for _, files in self.fs1.walk(search="breadth"):
            if "a.txt" in files:
                found_a = True
            if "c" in files:
                break
        assert found_a, "breadth search order was wrong"
        #  When searching depth-first, deep entries come first
        found_c = False
        for _, files in self.fs1.walk(search="depth"):
            if "c" in files:
                found_c = True
            if "a.txt" in files:
                break
        assert found_c, "depth search order was wrong: " + \
            str(list(self.fs1.walk(search="depth")))

    def test_walk_wildcard(self):
        self.fs1.setcontents('a.txt', b('hello'))
        self.fs1.setcontents('b.txt', b('world'))
        self.fs1.makeopendir('foo').setcontents('c', b('123'))
        self.fs1.makeopendir('.svn').setcontents('ignored', b(''))
        for dir_path, paths in self.fs1.walk(wildcard='*.txt'):
            for path in paths:
                self.assert_(path.endswith('.txt'))
        for dir_path, paths in self.fs1.walk(wildcard=lambda fn: fn.endswith('.txt')):
            for path in paths:
                self.assert_(path.endswith('.txt'))

    def test_walk_dir_wildcard(self):
        self.fs1.setcontents('a.txt', b('hello'))
        self.fs1.setcontents('b.txt', b('world'))
        self.fs1.makeopendir('foo').setcontents('c', b('123'))
        self.fs1.makeopendir('.svn').setcontents('ignored', b(''))
        for dir_path, paths in self.fs1.walk(dir_wildcard=lambda fn: not fn.endswith('.svn')):
            for path in paths:
                self.assert_('.svn' not in path)

    def test_walkfiles(self):
        self.fs1.makeopendir('bar').setcontents('a.txt', b('123'))
        self.fs1.makeopendir('foo').setcontents('b', b('123'))
        self.assertEquals(sorted(
            self.fs1.walkfiles()), ["/bar/a.txt", "/foo/b"])
        self.assertEquals(sorted(self.fs1.walkfiles(
            dir_wildcard="*foo*")), ["/foo/b"])
        self.assertEquals(sorted(self.fs1.walkfiles(
            wildcard="*.txt")), ["/bar/a.txt"])

    def test_walkdirs(self):
        self.fs1.makeopendir('bar').setcontents('a.txt', b('123'))
        self.fs1.makeopendir('foo').makeopendir(
            "baz").setcontents('b', b('123'))
        self.assertEquals(sorted(self.fs1.walkdirs()), [
                          "/", "/bar", "/foo", "/foo/baz"])
        self.assertEquals(sorted(self.fs1.walkdirs(
            wildcard="*foo*")), ["/", "/foo", "/foo/baz"])

    def test_unicode(self):
        alpha = u"\N{GREEK SMALL LETTER ALPHA}"
        beta = u"\N{GREEK SMALL LETTER BETA}"
        self.fs1.makedir(alpha)
        self.fs1.setcontents(alpha + "/a", b(''))
        self.fs1.setcontents(alpha + "/" + beta, b(''))
        self.assertTrue(self.check(alpha))
        self.assertEquals(sorted(self.fs1.listdir(alpha)), ["a", beta])

    def test_makedir(self):
        check = self.check
        self.fs1.makedir("a")
        self.assertTrue(check("a"))
        self.assertRaises(
            ParentDirectoryMissingError, self.fs1.makedir, "a/b/c")
        self.fs1.makedir("a/b/c", recursive=True)
        self.assert_(check("a/b/c"))
        self.fs1.makedir("foo/bar/baz", recursive=True)
        self.assert_(check("foo/bar/baz"))
        self.fs1.makedir("a/b/child")
        self.assert_(check("a/b/child"))
        self.assertRaises(DestinationExistsError, self.fs1.makedir, "/a/b")
        self.fs1.makedir("/a/b", allow_recreate=True)
        self.fs1.setcontents("/a/file", b(''))
        self.assertRaises(ResourceInvalidError, self.fs1.makedir, "a/file")

    def test_remove(self):
        self.fs1.setcontents("a.txt", b(''))
        self.assertTrue(self.check("a.txt"))
        self.fs1.remove("a.txt")
        self.assertFalse(self.check("a.txt"))
        self.assertRaises(ResourceNotFoundError, self.fs1.remove, "a.txt")
        self.fs1.makedir("dir1")
        self.assertRaises(ResourceInvalidError, self.fs1.remove, "dir1")
        self.fs1.setcontents("/dir1/a.txt", b(''))
        self.assertTrue(self.check("dir1/a.txt"))
        self.fs1.remove("dir1/a.txt")
        self.assertFalse(self.check("/dir1/a.txt"))

    def test_removedir(self):
        check = self.check
        self.fs1.makedir("a")
        self.assert_(check("a"))
        self.fs1.removedir("a")
        self.assertRaises(ResourceNotFoundError, self.fs1.removedir, "a")
        self.assert_(not check("a"))
        self.fs1.makedir("a/b/c/d", recursive=True)
        self.assertRaises(DirectoryNotEmptyError, self.fs1.removedir, "a/b")
        self.fs1.removedir("a/b/c/d")
        self.assert_(not check("a/b/c/d"))
        self.fs1.removedir("a/b/c")
        self.assert_(not check("a/b/c"))
        self.fs1.removedir("a/b")
        self.assert_(not check("a/b"))
        #  Test recursive removal of empty parent dirs
        self.fs1.makedir("foo/bar/baz", recursive=True)
        self.fs1.removedir("foo/bar/baz", recursive=True)
        self.assert_(not check("foo/bar/baz"))
        self.assert_(not check("foo/bar"))
        self.assert_(not check("foo"))
        self.fs1.makedir("foo/bar/baz", recursive=True)
        self.fs1.setcontents("foo/file.txt", b("please don't delete me"))
        self.fs1.removedir("foo/bar/baz", recursive=True)
        self.assert_(not check("foo/bar/baz"))
        self.assert_(not check("foo/bar"))
        self.assert_(check("foo/file.txt"))
        #  Ensure that force=True works as expected
        self.fs1.makedir("frollic/waggle", recursive=True)
        self.fs1.setcontents("frollic/waddle.txt", b("waddlewaddlewaddle"))
        self.assertRaises(DirectoryNotEmptyError, self.fs1.removedir, "frollic")
        self.assertRaises(
            ResourceInvalidError, self.fs1.removedir, "frollic/waddle.txt")
        self.fs1.removedir("frollic", force=True)
        self.assert_(not check("frollic"))
        #  Test removing unicode dirs
        kappa = u"\N{GREEK CAPITAL LETTER KAPPA}"
        self.fs1.makedir(kappa)
        self.assert_(self.fs1.isdir(kappa))
        self.fs1.removedir(kappa)
        self.assertRaises(ResourceNotFoundError, self.fs1.removedir, kappa)
        self.assert_(not self.fs1.isdir(kappa))
        self.fs1.makedir(pathjoin("test", kappa), recursive=True)
        self.assert_(check(pathjoin("test", kappa)))
        self.fs1.removedir("test", force=True)
        self.assert_(not check("test"))

    def test_rename(self):
        check = self.check
        # test renaming a file in the same directory
        self.fs1.setcontents("foo.txt", b("Hello, World!"))
        self.assert_(check("foo.txt"))
        self.fs1.rename("foo.txt", "bar.txt")
        self.assert_(check("bar.txt"))
        self.assert_(not check("foo.txt"))
        # test renaming a directory in the same directory
        self.fs1.makedir("dir_a")
        self.fs1.setcontents("dir_a/test.txt", b("testerific"))
        self.assert_(check("dir_a"))
        self.fs1.rename("dir_a", "dir_b")
        self.assert_(check("dir_b"))
        self.assert_(check("dir_b/test.txt"))
        self.assert_(not check("dir_a/test.txt"))
        self.assert_(not check("dir_a"))
        # test renaming a file into a different directory
        self.fs1.makedir("dir_a")
        self.fs1.rename("dir_b/test.txt", "dir_a/test.txt")
        self.assert_(not check("dir_b/test.txt"))
        self.assert_(check("dir_a/test.txt"))
        # test renaming a file into a non-existent  directory
        self.assertRaises(ParentDirectoryMissingError,
                          self.fs1.rename, "dir_a/test.txt", "nonexistent/test.txt")

    def test_info(self):
        test_str = b("Hello, World!")
        self.fs1.setcontents("info.txt", test_str)
        info = self.fs1.getinfo("info.txt")
        self.assertEqual(info['size'], len(test_str))
        self.fs1.desc("info.txt")
        self.assertRaises(ResourceNotFoundError, self.fs1.getinfo, "notafile")
        self.assertRaises(
            ResourceNotFoundError, self.fs1.getinfo, "info.txt/inval")

    def test_infokeys(self):
        test_str = b("Hello, World!")
        self.fs1.setcontents("info.txt", test_str)
        info = self.fs1.getinfo("info.txt")
        for k, v in info.iteritems():
            if not (k == 'asbytes' and callable(v)):
                self.assertEqual(self.fs1.getinfokeys('info.txt', k), {k: v})

        test_info = {}
        if 'modified_time' in info:
            test_info['modified_time'] = info['modified_time']
        if 'size' in info:
            test_info['size'] = info['size']
        self.assertEqual(self.fs1.getinfokeys('info.txt', 'size', 'modified_time'), test_info)
        self.assertEqual(self.fs1.getinfokeys('info.txt', 'thiscantpossiblyexistininfo'), {})

    def test_getsize(self):
        test_str = b("*") * 23
        self.fs1.setcontents("info.txt", test_str)
        size = self.fs1.getsize("info.txt")
        self.assertEqual(size, len(test_str))

    def test_movefile(self):
        check = self.check
        contents = b(
            "If the implementation is hard to explain, it's a bad idea.")

        def makefile(path):
            self.fs1.setcontents(path, contents)

        def checkcontents(path):
            check_contents = self.fs1.getcontents(path, "rb")
            self.assertEqual(check_contents, contents)
            return contents == check_contents

        self.fs1.makedir("foo/bar", recursive=True)
        makefile("foo/bar/a.txt")
        self.assert_(check("foo/bar/a.txt"))
        self.assert_(checkcontents("foo/bar/a.txt"))
        self.fs1.move("foo/bar/a.txt", "foo/b.txt")
        self.assert_(not check("foo/bar/a.txt"))
        self.assert_(check("foo/b.txt"))
        self.assert_(checkcontents("foo/b.txt"))

        self.fs1.move("foo/b.txt", "c.txt")
        self.assert_(not check("foo/b.txt"))
        self.assert_(check("/c.txt"))
        self.assert_(checkcontents("/c.txt"))

        makefile("foo/bar/a.txt")
        self.assertRaises(
            DestinationExistsError, self.fs1.move, "foo/bar/a.txt", "/c.txt")
        self.assert_(check("foo/bar/a.txt"))
        self.assert_(check("/c.txt"))
        self.fs1.move("foo/bar/a.txt", "/c.txt", overwrite=True)
        self.assert_(not check("foo/bar/a.txt"))
        self.assert_(check("/c.txt"))

    def test_movedir(self):
        check = self.check
        contents = b(
            "If the implementation is hard to explain, it's a bad idea.")

        def makefile(path):
            self.fs1.setcontents(path, contents)

        self.assertRaises(ResourceNotFoundError, self.fs1.movedir, "a", "b")
        self.fs1.makedir("a")
        self.fs1.makedir("b")
        makefile("a/1.txt")
        makefile("a/2.txt")
        makefile("a/3.txt")
        self.fs1.makedir("a/foo/bar", recursive=True)
        makefile("a/foo/bar/baz.txt")

        self.fs1.movedir("a", "copy of a")

        self.assert_(self.fs1.isdir("copy of a"))
        self.assert_(check("copy of a/1.txt"))
        self.assert_(check("copy of a/2.txt"))
        self.assert_(check("copy of a/3.txt"))
        self.assert_(check("copy of a/foo/bar/baz.txt"))

        self.assert_(not check("a/1.txt"))
        self.assert_(not check("a/2.txt"))
        self.assert_(not check("a/3.txt"))
        self.assert_(not check("a/foo/bar/baz.txt"))
        self.assert_(not check("a/foo/bar"))
        self.assert_(not check("a/foo"))
        self.assert_(not check("a"))

        self.fs1.makedir("a")
        self.assertRaises(
            DestinationExistsError, self.fs1.movedir, "copy of a", "a")
        self.fs1.movedir("copy of a", "a", overwrite=True)
        self.assert_(not check("copy of a"))
        self.assert_(check("a/1.txt"))
        self.assert_(check("a/2.txt"))
        self.assert_(check("a/3.txt"))
        self.assert_(check("a/foo/bar/baz.txt"))

    def test_cant_copy_from_os(self):
        sys_executable = os.path.abspath(os.path.realpath(sys.executable))
        self.assertRaises(FSError, self.fs1.copy, sys_executable, "py.exe")

    def test_copyfile(self):
        check = self.check
        contents = b(
            "If the implementation is hard to explain, it's a bad idea.")

        def makefile(path, contents=contents):
            self.fs1.setcontents(path, contents)

        def checkcontents(path, contents=contents):
            check_contents = self.fs1.getcontents(path, "rb")
            self.assertEqual(check_contents, contents)
            return contents == check_contents

        self.fs1.makedir("foo/bar", recursive=True)
        makefile("foo/bar/a.txt")
        self.assert_(check("foo/bar/a.txt"))
        self.assert_(checkcontents("foo/bar/a.txt"))
        # import rpdb2; rpdb2.start_embedded_debugger('password');
        self.fs1.copy("foo/bar/a.txt", "foo/b.txt")
        self.assert_(check("foo/bar/a.txt"))
        self.assert_(check("foo/b.txt"))
        self.assert_(checkcontents("foo/bar/a.txt"))
        self.assert_(checkcontents("foo/b.txt"))

        self.fs1.copy("foo/b.txt", "c.txt")
        self.assert_(check("foo/b.txt"))
        self.assert_(check("/c.txt"))
        self.assert_(checkcontents("/c.txt"))

        makefile("foo/bar/a.txt", b("different contents"))
        self.assert_(checkcontents("foo/bar/a.txt", b("different contents")))
        self.assertRaises(
            DestinationExistsError, self.fs1.copy, "foo/bar/a.txt", "/c.txt")
        self.assert_(checkcontents("/c.txt"))
        self.fs1.copy("foo/bar/a.txt", "/c.txt", overwrite=True)
        self.assert_(checkcontents("foo/bar/a.txt", b("different contents")))
        self.assert_(checkcontents("/c.txt", b("different contents")))

    def test_copydir(self):
        check = self.check
        contents = b(
            "If the implementation is hard to explain, it's a bad idea.")

        def makefile(path):
            self.fs1.setcontents(path, contents)

        def checkcontents(path):
            check_contents = self.fs1.getcontents(path)
            self.assertEqual(check_contents, contents)
            return contents == check_contents

        self.fs1.makedir("a")
        self.fs1.makedir("b")
        makefile("a/1.txt")
        makefile("a/2.txt")
        makefile("a/3.txt")
        self.fs1.makedir("a/foo/bar", recursive=True)
        makefile("a/foo/bar/baz.txt")

        self.fs1.copydir("a", "copy of a")
        self.assert_(check("copy of a/1.txt"))
        self.assert_(check("copy of a/2.txt"))
        self.assert_(check("copy of a/3.txt"))
        self.assert_(check("copy of a/foo/bar/baz.txt"))
        checkcontents("copy of a/1.txt")

        self.assert_(check("a/1.txt"))
        self.assert_(check("a/2.txt"))
        self.assert_(check("a/3.txt"))
        self.assert_(check("a/foo/bar/baz.txt"))
        checkcontents("a/1.txt")

        self.assertRaises(DestinationExistsError, self.fs1.copydir, "a", "b")
        self.fs1.copydir("a", "b", overwrite=True)
        self.assert_(check("b/1.txt"))
        self.assert_(check("b/2.txt"))
        self.assert_(check("b/3.txt"))
        self.assert_(check("b/foo/bar/baz.txt"))
        checkcontents("b/1.txt")

    def test_copydir_with_dotfile(self):
        check = self.check
        contents = b(
            "If the implementation is hard to explain, it's a bad idea.")

        def makefile(path):
            self.fs1.setcontents(path, contents)

        self.fs1.makedir("a")
        makefile("a/1.txt")
        makefile("a/2.txt")
        makefile("a/.hidden.txt")

        self.fs1.copydir("a", "copy of a")
        self.assert_(check("copy of a/1.txt"))
        self.assert_(check("copy of a/2.txt"))
        self.assert_(check("copy of a/.hidden.txt"))

        self.assert_(check("a/1.txt"))
        self.assert_(check("a/2.txt"))
        self.assert_(check("a/.hidden.txt"))

    def test_readwriteappendseek(self):
        def checkcontents(path, check_contents):
            read_contents = self.fs1.getcontents(path, "rb")
            self.assertEqual(read_contents, check_contents)
            return read_contents == check_contents
        test_strings = [b("Beautiful is better than ugly."),
                        b("Explicit is better than implicit."),
                        b("Simple is better than complex.")]
        all_strings = b("").join(test_strings)

        self.assertRaises(ResourceNotFoundError, self.fs1.open, "a.txt", "r")
        self.assert_(not self.fs1.exists("a.txt"))
        f1 = self.fs1.open("a.txt", "wb")
        pos = 0
        for s in test_strings:
            f1.write(s)
            pos += len(s)
            self.assertEqual(pos, f1.tell())
        f1.close()
        self.assert_(self.fs1.exists("a.txt"))
        self.assert_(checkcontents("a.txt", all_strings))

        f2 = self.fs1.open("b.txt", "wb")
        f2.write(test_strings[0])
        f2.close()
        self.assert_(checkcontents("b.txt", test_strings[0]))
        f3 = self.fs1.open("b.txt", "ab")
        # On win32, tell() gives zero until you actually write to the file
        # self.assertEquals(f3.tell(),len(test_strings[0]))
        f3.write(test_strings[1])
        self.assertEquals(f3.tell(), len(test_strings[0])+len(test_strings[1]))
        f3.write(test_strings[2])
        self.assertEquals(f3.tell(), len(all_strings))
        f3.close()
        self.assert_(checkcontents("b.txt", all_strings))
        f4 = self.fs1.open("b.txt", "wb")
        f4.write(test_strings[2])
        f4.close()
        self.assert_(checkcontents("b.txt", test_strings[2]))
        f5 = self.fs1.open("c.txt", "wb")
        for s in test_strings:
            f5.write(s+b("\n"))
        f5.close()
        f6 = self.fs1.open("c.txt", "rb")
        for s, t in zip(f6, test_strings):
            self.assertEqual(s, t+b("\n"))
        f6.close()
        f7 = self.fs1.open("c.txt", "rb")
        f7.seek(13)
        word = f7.read(6)
        self.assertEqual(word, b("better"))
        f7.seek(1, os.SEEK_CUR)
        word = f7.read(4)
        self.assertEqual(word, b("than"))
        f7.seek(-9, os.SEEK_END)
        word = f7.read(7)
        self.assertEqual(word, b("complex"))
        f7.close()
        self.assertEqual(self.fs1.getcontents("a.txt", "rb"), all_strings)

    def test_truncate(self):
        def checkcontents(path, check_contents):
            read_contents = self.fs1.getcontents(path, "rb")
            self.assertEqual(read_contents, check_contents)
            return read_contents == check_contents
        self.fs1.setcontents("hello", b("world"))
        checkcontents("hello", b("world"))
        self.fs1.setcontents("hello", b("hi"))
        checkcontents("hello", b("hi"))
        self.fs1.setcontents("hello", b("1234567890"))
        checkcontents("hello", b("1234567890"))
        with self.fs1.open("hello", "rb+") as f:
            f.truncate(7)
        checkcontents("hello", b("1234567"))
        with self.fs1.open("hello", "rb+") as f:
            f.seek(5)
            f.truncate()
        checkcontents("hello", b("12345"))

    def test_truncate_to_larger_size(self):
        with self.fs1.open("hello", "wb") as f:
            f.truncate(30)

        self.assertEquals(self.fs1.getsize("hello"), 30)

        # Some file systems (FTPFS) don't support both reading and writing
        if self.fs1.getmeta('file.read_and_write', True):
            with self.fs1.open("hello", "rb+") as f:
                f.seek(25)
                f.write(b("123456"))

            with self.fs1.open("hello", "rb") as f:
                f.seek(25)
                self.assertEquals(f.read(), b("123456"))

    def test_write_past_end_of_file(self):
        if self.fs1.getmeta('file.read_and_write', True):
            with self.fs1.open("write_at_end", "wb") as f:
                f.seek(25)
                f.write(b("EOF"))
            with self.fs1.open("write_at_end", "rb") as f:
                self.assertEquals(f.read(), b("\x00")*25 + b("EOF"))

    def test_with_statement(self):
        contents = b"testing the with statement"
        #  A successful 'with' statement
        with self.fs1.open('f.txt','wb-') as testfile:
            testfile.write(contents)
        self.assertEquals(self.fs1.getcontents('f.txt', 'rb'), contents)
        # A 'with' statement raising an error
        def with_error():
            with self.fs1.open('g.txt','wb-') as testfile:
                testfile.write(contents)
                raise ValueError
        self.assertRaises(ValueError, with_error)
        self.assertEquals(self.fs1.getcontents('g.txt', 'rb'), contents)

    def test_pickling(self):
        if self.fs1.getmeta('pickle_contents', True):
            self.fs1.setcontents("test1", b("hello world"))
            fs2 = pickle.loads(pickle.dumps(self.fs1))
            self.assert_(fs2.isfile("test1"))
            fs3 = pickle.loads(pickle.dumps(self.fs1, -1))
            self.assert_(fs3.isfile("test1"))
        else:
            # Just make sure it doesn't throw an exception
            fs2 = pickle.loads(pickle.dumps(self.fs1))

    def test_big_file(self):
        """Test handling of a big file (1MB)"""
        chunk_size = 1024 * 256
        num_chunks = 4

        def chunk_stream():
            """Generate predictable-but-randomy binary content."""
            r = random.Random(0)
            randint = r.randint
            int2byte = six.int2byte
            for _i in xrange(num_chunks):
                c = b("").join(int2byte(randint(
                    0, 255)) for _j in xrange(chunk_size//8))
                yield c * 8
                f = self.fs1.open("bigfile", "wb")
                try:
                    for chunk in chunk_stream():
                        f.write(chunk)
                finally:
                    f.close()
                chunks = chunk_stream()
                f = self.fs1.open("bigfile", "rb")
                try:
                    try:
                        while True:
                            if chunks.next() != f.read(chunk_size):
                                assert False, "bigfile was corrupted"
                    except StopIteration:
                        if f.read() != b(""):
                            assert False, "bigfile was corrupted"
                finally:
                    f.close()

    def test_settimes(self):
        def cmp_datetimes(d1, d2):
            """Test datetime objects are the same to within the timestamp accuracy"""
            dts1 = time.mktime(d1.timetuple())
            dts2 = time.mktime(d2.timetuple())
            return int(dts1) == int(dts2)
        d1 = datetime.datetime(2010, 6, 20, 11, 0, 9, 987699)
        d2 = datetime.datetime(2010, 7, 5, 11, 0, 9, 500000)
        self.fs1.setcontents('/dates.txt', b('check dates'))
        # If the implementation supports settimes, check that the times
        # can be set and then retrieved
        try:
            self.fs1.settimes('/dates.txt', d1, d2)
        except UnsupportedError:
            pass
        else:
            info = self.fs1.getinfo('/dates.txt')
            self.assertTrue(cmp_datetimes(d1, info['accessed_time']))
            self.assertTrue(cmp_datetimes(d2, info['modified_time']))

    def test_removeroot(self):
        self.assertRaises(RemoveRootError, self.fs1.removedir, "/")

    def test_zero_read(self):
        """Test read(0) returns empty string"""
        self.fs1.setcontents('foo.txt', b('Hello, World'))
        with self.fs1.open('foo.txt', 'rb') as f:
            self.assert_(len(f.read(0)) == 0)
        with self.fs1.open('foo.txt', 'rt') as f:
            self.assert_(len(f.read(0)) == 0)

# May be disabled - see end of file


class ThreadingTestCases(object):
    """Testcases for thread-safety of FS implementations."""

    #  These are either too slow to be worth repeating,
    #  or cannot possibly break cross-thread.
    _dont_retest = ("test_pickling", "test_multiple_overwrite",)

    __lock = threading.RLock()

    def _yield(self):
        # time.sleep(0.001)
        # Yields without a delay
        time.sleep(0)

    def _lock(self):
        self.__lock.acquire()

    def _unlock(self):
        self.__lock.release()

    def _makeThread(self, func, errors):
        def runThread():
            try:
                func()
            except Exception:
                errors.append(sys.exc_info())
        thread = threading.Thread(target=runThread)
        thread.daemon = True
        return thread

    def _runThreads(self, *funcs):
        check_interval = sys.getcheckinterval()
        sys.setcheckinterval(1)
        try:
            errors = []
            threads = [self._makeThread(f, errors) for f in funcs]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            for (c, e, t) in errors:
                raise e, None, t
        finally:
            sys.setcheckinterval(check_interval)

    def test_setcontents_threaded(self):
        def setcontents(name, contents):
            f = self.fs1.open(name, "wb")
            self._yield()
            try:
                f.write(contents)
                self._yield()
            finally:
                f.close()

        def thread1():
            c = b("thread1 was 'ere")
            setcontents("thread1.txt", c)
            self.assertEquals(self.fs1.getcontents("thread1.txt", 'rb'), c)

        def thread2():
            c = b("thread2 was 'ere")
            setcontents("thread2.txt", c)
            self.assertEquals(self.fs1.getcontents("thread2.txt", 'rb'), c)
        self._runThreads(thread1, thread2)

    def test_setcontents_threaded_samefile(self):
        def setcontents(name, contents):
            f = self.fs1.open(name, "wb")
            self._yield()
            try:
                f.write(contents)
                self._yield()
            finally:
                f.close()

        def thread1():
            c = b("thread1 was 'ere")
            setcontents("threads.txt", c)
            self._yield()
            self.assertEquals(self.fs1.listdir("/"), ["threads.txt"])

        def thread2():
            c = b("thread2 was 'ere")
            setcontents("threads.txt", c)
            self._yield()
            self.assertEquals(self.fs1.listdir("/"), ["threads.txt"])

        def thread3():
            c = b("thread3 was 'ere")
            setcontents("threads.txt", c)
            self._yield()
            self.assertEquals(self.fs1.listdir("/"), ["threads.txt"])
        try:
            self._runThreads(thread1, thread2, thread3)
        except ResourceLockedError:
            # that's ok, some implementations don't support concurrent writes
            pass

    def test_cases_in_separate_dirs(self):
        class TestCases_in_subdir(self.__class__, unittest.TestCase):
            """Run all testcases against a subdir of self.fs1"""
            def __init__(this, subdir):
                super(TestCases_in_subdir, this).__init__("test_listdir")
                this.subdir = subdir
                for meth in dir(this):
                    if not meth.startswith("test_"):
                        continue
                    if meth in self._dont_retest:
                        continue
                    if not hasattr(FSTestCases, meth):
                        continue
                    if self.fs1.exists(subdir):
                        self.fs1.removedir(subdir, force=True)
                    self.assertFalse(self.fs1.isdir(subdir))
                    self.assertTrue(self.fs1.isdir("/"))
                    self.fs1.makedir(subdir)
                    self._yield()
                    getattr(this, meth)()

            @property
            def fs1(this):
                return self.fs1.opendir(this.subdir)

            def check(this, p):
                return self.check(pathjoin(this.subdir, relpath(p)))

        def thread1():
            TestCases_in_subdir("thread1")

        def thread2():
            TestCases_in_subdir("thread2")

        def thread3():
            TestCases_in_subdir("thread3")
        self._runThreads(thread1, thread2, thread3)

    def test_makedir_winner(self):
        errors = []

        def makedir():
            try:
                self.fs1.makedir("testdir")
            except DestinationExistsError, e:
                errors.append(e)

        def makedir_noerror():
            try:
                self.fs1.makedir("testdir", allow_recreate=True)
            except DestinationExistsError, e:
                errors.append(e)

        def removedir():
            try:
                self.fs1.removedir("testdir")
            except (ResourceNotFoundError, ResourceLockedError), e:
                errors.append(e)
        # One thread should succeed, one should error
        self._runThreads(makedir, makedir)
        self.assertEquals(len(errors), 1)
        self.fs1.removedir("testdir")
        # One thread should succeed, two should error
        errors = []
        self._runThreads(makedir, makedir, makedir)
        if len(errors) != 2:
            raise AssertionError(errors)
        self.fs1.removedir("testdir")
        # All threads should succeed
        errors = []
        self._runThreads(makedir_noerror, makedir_noerror, makedir_noerror)
        self.assertEquals(len(errors), 0)
        self.assertTrue(self.fs1.isdir("testdir"))
        self.fs1.removedir("testdir")
        # makedir() can beat removedir() and vice-versa
        errors = []
        self._runThreads(makedir, removedir)
        if self.fs1.isdir("testdir"):
            self.assertEquals(len(errors), 1)
            self.assertFalse(isinstance(errors[0], DestinationExistsError))
            self.fs1.removedir("testdir")
        else:
            self.assertEquals(len(errors), 0)

    def test_concurrent_copydir(self):
        self.fs1.makedir("a")
        self.fs1.makedir("a/b")
        self.fs1.setcontents("a/hello.txt", b("hello world"))
        self.fs1.setcontents("a/guido.txt", b("is a space alien"))
        self.fs1.setcontents("a/b/parrot.txt", b("pining for the fiords"))

        def copydir():
            self._yield()
            self.fs1.copydir("a", "copy of a")

        def copydir_overwrite():
            self._yield()
            self.fs1.copydir("a", "copy of a", overwrite=True)
        # This should error out since we're not overwriting
        self.assertRaises(
            DestinationExistsError, self._runThreads, copydir, copydir)
        self.assert_(self.fs1.isdir('a'))
        self.assert_(self.fs1.isdir('a'))
        copydir_overwrite()
        self.assert_(self.fs1.isdir('a'))
        # This should run to completion and give a valid state, unless
        # files get locked when written to.
        try:
            self._runThreads(copydir_overwrite, copydir_overwrite)
        except ResourceLockedError:
            pass
        self.assertTrue(self.fs1.isdir("copy of a"))
        self.assertTrue(self.fs1.isdir("copy of a/b"))
        self.assertEqual(self.fs1.getcontents(
            "copy of a/b/parrot.txt", 'rb'), b("pining for the fiords"))
        self.assertEqual(self.fs1.getcontents(
            "copy of a/hello.txt", 'rb'), b("hello world"))
        self.assertEqual(self.fs1.getcontents(
            "copy of a/guido.txt", 'rb'), b("is a space alien"))

    def test_multiple_overwrite(self):
        contents = [b("contents one"), b(
            "contents the second"), b("number three")]

        def thread1():
            for i in xrange(30):
                for c in contents:
                    self.fs1.setcontents("thread1.txt", c)
                    self.assertEquals(self.fs1.getsize("thread1.txt"), len(c))
                    self.assertEquals(self.fs1.getcontents(
                        "thread1.txt", 'rb'), c)

        def thread2():
            for i in xrange(30):
                for c in contents:
                    self.fs1.setcontents("thread2.txt", c)
                    self.assertEquals(self.fs1.getsize("thread2.txt"), len(c))
                    self.assertEquals(self.fs1.getcontents(
                        "thread2.txt", 'rb'), c)
        self._runThreads(thread1, thread2)

# Uncomment to temporarily disable threading tests
# class ThreadingTestCases(object):
#    _dont_retest = ()
