import logging
import os
from astropy.io import fits

from pytel.object import get_object


log = logging.getLogger(__name__)


class VFSFile:
    pass


class VirtualFileSystem:
    """Base for a virtual file system."""

    def __init__(self, roots: dict = None, compression: dict = None, *args, **kwargs):
        """Create a new VFS.

        Args:
            roots: Dictionary containing roots.
            compression: Dictionary containing files that should be compressed.
        """

        # store
        self._roots = {} if roots is None else roots
        self._compression = {'.gz': '/bin/gzip'} if compression is None else compression

    @staticmethod
    def split_root(path: str) -> tuple:
        """Splits the root from the rest of the path.

        Args:
            path (str): Path to split.

        Returns:
            (tuple) Tuple (root, filename).
        """

        # remove leading slash
        if path.startswith('/'):
            path = path[1:]

        # no more slash left?
        if '/' not in path:
            raise ValueError('No valid path with a root.')

        # get position of first slash and split
        pos = path.index('/')
        root = path[:pos]
        filename = path[pos + 1:]

        # return it
        return root, filename

    def open_file(self, filename: str, mode: str, compression: bool = None) -> VFSFile:
        """Open a file. The handling class is chosen depending on the rootse in the filename.

        Args:
            filename (str): Name of file to open.
            mode (str): Opening mode.
            compression (bool): Automatically (de)compress data if True. Automatically determine from filename if None.

        Returns:
            (IOBase) File like object for given file.
        """
        from .gzippipe import GzipReader, GzipWriter

        # split root
        root, filename = VirtualFileSystem.split_root(filename)

        # does root exist?
        if root not in self._roots:
            raise ValueError('Could not find root {0} for file.'.format(root))

        # create file object
        fd = get_object(self._roots[root], name=filename, mode=mode)

        # compression?
        if compression or (compression is None and os.path.splitext(filename)[1] in self._compression):
            # create pipe
            if 'w' in mode:
                fd = GzipWriter(fd, close_fd=True)
            else:
                fd = GzipReader(fd, close_fd=True)

        # return it
        return fd

    def download_fits_image(self, filename) -> fits.PrimaryHDU:
        """Convenience function that wraps around open_file() to download a FITS file and put it into a astropy FITS
        structure.

        Args:
            filename: Name of file to download.

        Returns:
            A PrimaryHDU containing the FITS file.
        """
        with self.open_file(filename, 'rb') as f:
            tmp = fits.open(f)
            hdu = fits.PrimaryHDU(data=tmp[0].data, header=tmp[0].header)
            tmp.close()
            return hdu


__all__ = ['VirtualFileSystem', 'VFSFile']
