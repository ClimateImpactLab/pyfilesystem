"""
fs1.expose.django
================

Use an FS object for Django File Storage

This module exposes the class "FSStorage", a simple adapter for using FS
objects as Django storage objects.  Simply include the following lines
in your settings.py::

    DEFAULT_FILE_STORAGE = fs1.expose.django_storage.FSStorage
    DEFAULT_FILE_STORAGE_FS = OSFS('foo/bar')  # Or whatever FS


"""

from django.conf import settings
from django.core.files.storage import Storage
from django.core.files import File

from fs1.path import abspath, dirname
from fs1.errors import convert_fs_errors, ResourceNotFoundError

class FSStorage(Storage):
    """Expose an FS object as a Django File Storage object."""

    def __init__(self, fs1=None, base_url=None):
        """
        :param fs1: an FS object
        :param base_url: The url to prepend to the path

        """
        if fs1 is None:
            fs1 = settings.DEFAULT_FILE_STORAGE_FS
        if base_url is None:
            base_url = settings.MEDIA_URL
        base_url = base_url.rstrip('/')
        self.fs1 = fs1
        self.base_url = base_url

    def exists(self, name):
        return self.fs1.isfile(name)

    def path(self, name):
        path = self.fs1.getsyspath(name)
        if path is None:
            raise NotImplementedError
        return path

    @convert_fs_errors
    def size(self, name):
        return self.fs1.getsize(name)

    @convert_fs_errors
    def url(self, name):
        return self.base_url + abspath(name)

    @convert_fs_errors
    def _open(self, name, mode):
        return File(self.fs1.open(name, mode))

    @convert_fs_errors
    def _save(self, name, content):
        self.fs1.makedir(dirname(name), allow_recreate=True, recursive=True)
        self.fs1.setcontents(name, content)
        return name

    @convert_fs_errors
    def delete(self, name):
        try:
            self.fs1.remove(name)
        except ResourceNotFoundError:
            pass


