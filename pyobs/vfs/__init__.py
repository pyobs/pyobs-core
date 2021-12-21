"""
A virtual file system (VFS) is a convenient way for allowing access to different resources with a  common interface.
It also makes it easy to change the actual place of storage without any changes to the code. In *pyobs*, a path into
the VFS looks like a normal path on a Unix-like system::

    /path/to/file.ext

To be more precise, a path is built like this::

    /<root>/<path>/<filename>

where ``<root>`` indicates, which VFS to use, ``<path>`` is the path within that VFS and `<filename>` is the actual
filename.

The available roots in the *pyobs* VFS are usually defined in the configuration file like this::

    vfs:
        root1:
            class: VfsClass1
        root2:
            class: VfsClass2

With this configuration, all filenames that start with ``/root1/`` (e.g. ``/root1/path/filename.ext``) are handled
by ``VfsClass1``, while all filenames starting with ``/root2/`` use ``VfsClass2``. Both defined classes can have
additional parameters, which should also be given in the configuration.

With this example, one can easily see the advantages of using a VFS:

    1. File access to all roots look similar, we always open a filename like ``/root/path/file.ext``.

    2. Changing the handling class for one of the roots changes the way we access a file. For instance, if
       a file was always stored locally, but now we want to change that to a location using a SSH location, this can
       easily be accomplished by simply changing the configuration.

    3. Another advantage that we have not mentioned before is, that the same roots can use different handling classes on
       different machines. See below for details.

Imagine a file ``/storage/file.ext`` that maps to a local file on machine A, i.e. ``storage`` uses a handling class
that simply changes the filename to a local filename. On machine B we can now define the same root ``storage``, but use
a different handling class that, e.g., accesses the file via SSH. Still, the filename would be the same on both
machines. So A could store a file as ``/storage/file.ext``, send the filename to B, which then can access the file
via the same filename.

Currently supported are these types of file access:
    - :class:`~pyobs.vfs.LocalFile`: Local file on the machine the module is running on.
    - :class:`~pyobs.vfs.HttpFile`: File on a HTTP server.
    - :class:`~pyobs.vfs.MemoryFile`: File in memory.
    - :class:`~pyobs.vfs.SSHFile`: File on different machine that is accessible via SSH.
    - :class:`~pyobs.vfs.TarFile`: Wrapper for a dynamically created TAR file. Can only be read from.
    - :class:`~pyobs.vfs.TempFile`: Temporary file that will be deleted after being closed.
    - :class:`~pyobs.vfs.ArchiveFile`: Wrapper for a file in the :ref:`pyobs-archive` image archive.

The base class for all of these classes is :class:`~pyobs.vfs.VFSFile`.

"""
__title__ = 'Virtual File System'

from .vfs import VirtualFileSystem
from .file import VFSFile
from .localfile import LocalFile
from .httpfile import HttpFile
from .memfile import MemoryFile
from .sshfile import SSHFile
from .tempfile import TempFile
from .archivefile import ArchiveFile


__all__ = ['VirtualFileSystem', 'VFSFile', 'LocalFile', 'HttpFile', 'MemoryFile', 'SSHFile', 'TempFile', 'ArchiveFile']
