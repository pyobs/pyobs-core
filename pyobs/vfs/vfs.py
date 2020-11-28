import io
import logging
import os
from astropy.io import fits
import pandas as pd

from pyobs.object import get_object, get_class_from_string
from pyobs.utils.images import Image

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

        # if no root for 'pyobs' is given, add one
        if 'pyobs' not in self._roots:
            self._roots['pyobs'] = {
                'class': 'pyobs.vfs.LocalFile',
                'root': os.path.expanduser('~/.pyobs/')
            }

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

    def read_fits_image(self, filename) -> fits.PrimaryHDU:
        """Convenience function that wraps around open_file() to read a FITS file and put it into a astropy FITS
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

    def read_image(self, filename) -> Image:
        """Convenience function that wraps around open_file() to read an Image.

        Args:
            filename: Name of file to download.

        Returns:
            An image object
        """
        with self.open_file(filename, 'rb') as f:
            return Image.from_bytes(f.read())

    def write_image(self, filename: str, image: Image, *args, **kwargs):
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            image: Image to write.
        """

        # open file
        with self.open_file(filename, 'wb') as cache:
            image.writeto(cache, *args, **kwargs)

    def read_csv(self, filename: str, *args, **kwargs) -> pd.DataFrame:
        """Convenience function for reading a CSV file into a DataFrame.

        Args:
            filename: Name of file to read.

        Returns:
            DataFrame with content of file.
        """

        try:
            # open file
            with self.open_file(filename, 'r') as f:
                # read data and return it
                return pd.read_csv(f, *args, **kwargs)

        except pd.errors.EmptyDataError:
            # on error, return empty dataframe
            return pd.DataFrame()

    def write_csv(self, df: pd.DataFrame, filename: str, *args, **kwargs):
        """Convenience function for writing a CSV file from a DataFrame.

        Args:
            df: DataFrame to write.
            filename: Name of file to write.
        """

        with self.open_file(filename, 'w') as f:
            # create a StringIO as temporary write target
            with io.StringIO() as sio:
                # write table to sio
                df.to_csv(sio, *args, **kwargs)

                # and write all content to file
                f.write(sio.getvalue().encode('utf8'))

    def find(self, path: str, pattern: str):
        """Find a file in the given path.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.

        Returns:
            List of found files.
        """

        # split root
        if not path.endswith('/'):
            path += '/'
        root, path = VirtualFileSystem.split_root(path)

        # get root class
        klass = get_class_from_string(self._roots[root]['class'])

        # get find method
        find = getattr(klass, 'find')

        # and call it
        return find(path, pattern, **self._roots[root])

    def exists(self, path: str) -> bool:
        """Checks, whether a given path or file exists.

        Args:
            path: Path to check.

        Returns:
            Whether it exists or not
        """

        # split root
        if not path.endswith('/'):
            path += '/'
        root, path = VirtualFileSystem.split_root(path)

        # get root class
        klass = get_class_from_string(self._roots[root]['class'])

        # get exists method
        exists = getattr(klass, 'exists')

        # and call it
        return exists(path, **self._roots[root])


__all__ = ['VirtualFileSystem', 'VFSFile']
