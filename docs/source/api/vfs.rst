Virtual File System (pyobs.vfs)
-------------------------------

.. automodule:: pyobs.vfs

In a distributed *pyobs* system, modules typically run on different machines — a camera controller on one
computer, an image pipeline on another, a scheduler on a third. The Virtual File System (VFS) lets all of
them read and write files using the same logical paths, regardless of where the data physically lives.

Each VFS path starts with a **root** — a named prefix that maps to a specific storage backend. For example,
a path like ``/cache/image_001.fits`` uses the root ``cache``, which might point to a local directory on one
machine and an HTTP file cache on another. The calling code never needs to know the difference.


Configuration
^^^^^^^^^^^^^

The VFS is configured in YAML under a ``vfs`` key::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.LocalFile
          root: /data/pyobs/cache

This maps ``/cache/...`` to local files under ``/data/pyobs/cache``. On a different machine that needs to
read the same files over HTTP::

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        cache:
          class: pyobs.vfs.HttpFile
          download: https://camera-host.example.com/filecache/

Both machines use identical paths in their code — ``/cache/image_001.fits`` — and the VFS handles the
transport transparently.

Two roots are always available by default even without explicit configuration:

- ``/pyobs/`` → ``/opt/pyobs/storage/`` (local)
- ``/robotic/`` → ``/opt/pyobs/robotic/`` (local)


Reading and writing files
^^^^^^^^^^^^^^^^^^^^^^^^^

The primary interface is :meth:`~pyobs.vfs.VirtualFileSystem.open_file`, which returns a :class:`~pyobs.vfs.VFSFile`
that supports async context manager usage::

    async with self.vfs.open_file("/cache/image_001.fits", "rb") as f:
        data = await f.read()

For common file types, :class:`~pyobs.vfs.VirtualFileSystem` provides convenience methods that wrap
``open_file`` automatically:

- :meth:`~pyobs.vfs.VirtualFileSystem.read_image` / :meth:`~pyobs.vfs.VirtualFileSystem.write_image` — :class:`~pyobs.images.Image` objects
- :meth:`~pyobs.vfs.VirtualFileSystem.read_fits` / :meth:`~pyobs.vfs.VirtualFileSystem.write_fits` — raw FITS HDU lists
- :meth:`~pyobs.vfs.VirtualFileSystem.read_csv` / :meth:`~pyobs.vfs.VirtualFileSystem.write_csv` — pandas DataFrames
- :meth:`~pyobs.vfs.VirtualFileSystem.read_yaml` / :meth:`~pyobs.vfs.VirtualFileSystem.write_yaml` — dicts

Inside any :class:`~pyobs.object.Object` or :class:`~pyobs.modules.Module`, the VFS is available via
``self.vfs``::

    image = await self.vfs.read_image("/cache/image_001.fits")


File access classes
^^^^^^^^^^^^^^^^^^^

Each root in the VFS configuration maps to one of these classes:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Class
     - Use case
   * - :class:`~pyobs.vfs.LocalFile`
     - Files on the local filesystem. The most common choice for the machine that writes data.
   * - :class:`~pyobs.vfs.HttpFile`
     - Files served over HTTP, typically via :class:`~pyobs.modules.utils.HttpFileCache`. Use on machines
       that need to read files produced elsewhere.
   * - :class:`~pyobs.vfs.SSHFile`
     - Files on a remote machine accessed over SSH/SCP. Suitable when HTTP caching is not available.
   * - :class:`~pyobs.vfs.SFTPFile`
     - Files on a remote machine accessed over SFTP.
   * - :class:`~pyobs.vfs.SMBFile`
     - Files on a Windows share (SMB/CIFS).
   * - :class:`~pyobs.vfs.MemoryFile`
     - In-memory file storage. Useful for testing or short-lived intermediate data.
   * - :class:`~pyobs.vfs.TempFile`
     - Temporary files on the local filesystem, cleaned up automatically.
   * - :class:`~pyobs.vfs.ArchiveFile`
     - Files stored in a *pyobs* archive service.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.vfs.VirtualFileSystem
   :members:

.. autoclass:: pyobs.vfs.VFSFile
   :members:

.. autoclass:: pyobs.vfs.LocalFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.HttpFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.SSHFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.SFTPFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.SMBFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.MemoryFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.TempFile
   :members:
   :show-inheritance:

.. autoclass:: pyobs.vfs.ArchiveFile
   :members:
   :show-inheritance: