
import unittest
import sys
import os, os.path
import socket
import threading
import time

from fs1.tests import FSTestCases, ThreadingTestCases
from fs1.tempfs import TempFS
from fs1.osfs import OSFS
from fs1.memoryfs import MemoryFS
from fs1.path import *
from fs1.errors import *

from fs1 import rpcfs
from fs1.expose.xmlrpc import RPCFSServer

import six
from six import PY3, b


class TestRPCFS(unittest.TestCase, FSTestCases, ThreadingTestCases):

    def makeServer(self,fs1,addr):
        return RPCFSServer(fs1,addr,logRequests=False)

    def startServer(self):
        port = 3000
        self.temp_fs = TempFS()
        self.server = None

        self.serve_more_requests = True
        self.server_thread = threading.Thread(target=self.runServer)
        self.server_thread.setDaemon(True)

        self.start_event = threading.Event()
        self.end_event = threading.Event()

        self.server_thread.start()

        self.start_event.wait()

    def runServer(self):
        """Run the server, swallowing shutdown-related execptions."""

        port = 3000
        while not self.server:
            try:
                self.server = self.makeServer(self.temp_fs,("127.0.0.1",port))
            except socket.error, e:
                if e.args[1] == "Address already in use":
                    port += 1
                else:
                    raise
        self.server_addr = ("127.0.0.1", port)

        self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.start_event.set()

        try:
            #self.server.serve_forever()
            while self.serve_more_requests:
                self.server.handle_request()
        except Exception, e:
            pass

        self.end_event.set()

    def setUp(self):
        self.startServer()
        self.fs1 = rpcfs.RPCFS("http://%s:%d" % self.server_addr)

    def tearDown(self):
        self.serve_more_requests = False

        try:
            self.bump()
            self.server.server_close()
        except Exception:
            pass
        #self.server_thread.join()
        self.temp_fs.close()

    def bump(self):
        host, port = self.server_addr
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, cn, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(.1)
                sock.connect(sa)
                sock.send(b("\n"))
            except socket.error, e:
                pass
            finally:
                if sock is not None:
                    sock.close()
