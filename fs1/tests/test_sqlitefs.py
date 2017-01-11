try:
    from fs1.contrib.sqlitefs import SqliteFS
except ImportError:
    SqliteFS = None
from fs1.tests import FSTestCases
import unittest

import os

if SqliteFS:
    class TestSqliteFS(unittest.TestCase, FSTestCases):
        def setUp(self):
            self.fs1 = SqliteFS("sqlitefs.db")
        def tearDown(self):
            os.remove('sqlitefs.db')


