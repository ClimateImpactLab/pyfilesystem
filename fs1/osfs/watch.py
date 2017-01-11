"""
fs1.osfs.watch
=============

Change watcher support for OSFS

"""

import os
import sys
import errno
import threading

from fs1.errors import *
from fs1.path import *
from fs1.watch import *

OSFSWatchMixin = None

#  Try using native implementation on win32
if sys.platform == "win32":
    try:
        from fs1.osfs.watch_win32 import OSFSWatchMixin
    except ImportError:
        pass

#  Try using pyinotify if available
if OSFSWatchMixin is None:
    try:
        from fs1.osfs.watch_inotify import OSFSWatchMixin
    except ImportError:
        pass

#  Fall back to raising UnsupportedError
if OSFSWatchMixin is None:
    class OSFSWatchMixin(object):
        def __init__(self, *args, **kwargs):
            super(OSFSWatchMixin, self).__init__(*args, **kwargs)
        def add_watcher(self,*args,**kwds):
            raise UnsupportedError
        def del_watcher(self,watcher_or_callback):
            raise UnsupportedError


