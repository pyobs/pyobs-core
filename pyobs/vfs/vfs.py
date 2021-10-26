import io
import logging
import os
from typing import Optional, Dict, Any, Tuple, cast, IO, List

import yaml
from astropy.io import fits
import pandas as pd

from pyobs.images import Image

log = logging.getLogger(__name__)


class VFSFile(io.RawIOBase):
    """Base class for all VFS file classes."""
    __module__ = 'pyobs.vfs'

    def __enter__(self) -> 'VFSFile':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...


class VirtualFileSystem(object):
    """Base for a virtual file system."""
    __module__ = 'pyobs.vfs'

    def __init__(self, roots: Optional[Dict[str, Any]] = None, **kwargs: Any):
        """Create a new VFS.

        Args:
            roots: Dictionary containing roots, see :mod:`~pyobs.vfs` for examples.
        """

        # if no root for 'pyobs' is given, add one
        self._roots: Dict[str, Any] = {
            'pyobs': {
                'class': 'pyobs.vfs.LocalFile',
                'root': os.path.expanduser('~/.pyobs/')
            }
        }
        if roots is not None:
            self._roots.update(roots)

    @staticmethod
    def split_root(path: str) -> Tuple[str, str]:
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

    def open_file(self, filename: str, mode: str) -> VFSFile:
        """Open a file. The handling class is chosen depending on the rootse in the filename.

        Args:
            filename (str): Name of file to open.
            mode (str): Opening mode.

        Returns:
            (IOBase) File like object for given file.
        """
        # split root
        root, filename = VirtualFileSystem.split_root(filename)

        # does root exist?
        if root not in self._roots:
            raise ValueError('Could not find root {0} for file.'.format(root))

        # create file object
        from pyobs.object import get_object
        fd = get_object(self._roots[root], object_class=VFSFile, name=filename, mode=mode)

        # return it
        return fd

    def read_fits_image(self, filename: str) -> fits.PrimaryHDU:
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

    def read_image(self, filename: str) -> Image:
        """Convenience function that wraps around open_file() to read an Image.

        Args:
            filename: Name of file to download.

        Returns:
            An image object
        """
        with self.open_file(filename, 'rb') as f:
            return Image.from_bytes(f.read())

    def write_image(self, filename: str, image: Image, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            image: Image to write.
        """

        # open file
        with self.open_file(filename, 'wb') as cache:
            image.writeto(cache, *args, **kwargs)

    def read_csv(self, filename: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
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

    def write_csv(self, df: pd.DataFrame, filename: str, *args: Any, **kwargs: Any) -> None:
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

    def read_yaml(self, filename: str) -> Dict[str, Any]:
        """Convenience function for reading a YAML file into a dict.

        Args:
            filename: Name of file to read.

        Returns:
            Content of file.
        """

        # open file
        with self.open_file(filename, 'r') as f:
            # read YAML
            return cast(Dict[str, Any], yaml.safe_load(cast(IO[bytes], f)))

    def write_yaml(self, data: Dict[str, Any], filename: str) -> None:
        """Convenience function for writing a YAML file from a dict.

        Args:
            data: dict to write.
            filename: Name of file to write.
        """

        # open file
        with self.open_file(filename, 'w') as f:
            # create StringIO as temp storage
            with io.StringIO() as sio:
                # dump to StringIO
                yaml.dump(data, sio)

                # write file from StringIO
                f.write(bytes(sio.getvalue(), 'utf8'))

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
        from pyobs.object import get_class_from_string
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
        from pyobs.object import get_class_from_string
        klass = get_class_from_string(self._roots[root]['class'])

        # get exists method
        exists = getattr(klass, 'exists')

        # and call it
        return exists(path, **self._roots[root])


__all__ = ['VirtualFileSystem', 'VFSFile']
