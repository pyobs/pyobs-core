"""
TODO: write doc
"""
__title__ = 'Virtual File System'

from .vfs import VirtualFileSystem, VFSFile
from .localfile import LocalFile
from .httpfile import HttpFile
from .memfile import MemoryFile
from .sshfile import SSHFile
from .tarfile import TarFile
from .tempfile import TempFile
from .gzippipe import GzipReader, GzipWriter
from .archivefile import ArchiveFile
