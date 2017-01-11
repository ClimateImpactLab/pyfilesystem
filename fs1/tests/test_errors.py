# -*- encoding: utf-8 -*-
"""

  fs1.tests.test_errors:  testcases for the fs1 error classes functions

"""


import unittest
import fs1.tests
from fs1.errors import *
import pickle

from fs1.path import *

class TestErrorPickling(unittest.TestCase):

    def test_pickling(self):
        def assert_dump_load(e):
            e2 = pickle.loads(pickle.dumps(e))
            self.assertEqual(e.__dict__,e2.__dict__)
        assert_dump_load(FSError())
        assert_dump_load(PathError("/some/path"))
        assert_dump_load(ResourceNotFoundError("/some/other/path"))
        assert_dump_load(UnsupportedError("makepony"))


class TestFSError(unittest.TestCase):

    def test_unicode_representation_of_error_with_non_ascii_characters(self):
        path_error = PathError('/Shïrê/Frødø')
        _ = unicode(path_error)