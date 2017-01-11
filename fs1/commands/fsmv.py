#!/usr/bin/env python

from fs1.utils import movefile, movefile_non_atomic, contains_files
from fs1.commands import fscp
import sys

class FSmv(fscp.FScp):

    usage = """fsmv [OPTION]... [SOURCE] [DESTINATION]
Move files from SOURCE to DESTINATION"""

    def get_verb(self):
        return 'moving...'

    def get_action(self):
        if self.options.threads > 1:
            return movefile_non_atomic
        else:
            return movefile

    def post_actions(self):
        for fs1, dirpath in self.root_dirs:
            if not contains_files(fs1, dirpath):
                fs1.removedir(dirpath, force=True)

def run():
    return FSmv().run()

if __name__ == "__main__":
    sys.exit(run())
