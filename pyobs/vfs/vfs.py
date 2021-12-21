import asyncio
import io
import logging
import os
from functools import partial
from typing import Optional, Dict, Any, Tuple, cast, IO
import yaml
from astropy.io import fits
import pandas as pd

from pyobs.images import Image
from .file import VFSFile


log = logging.getLogger(__name__)


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

    async def read_fits(self, filename: str) -> fits.HDUList:
        """Convenience function that wraps around open_file() to read a FITS file and put it into a astropy FITS
        structure.

        Args:
            filename: Name of file to download.

        Returns:
            A PrimaryHDU containing the FITS file.
        """
        with self.open_file(filename, 'rb') as f:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, f.readall)
            return fits.HDUList.fromstring(data)

    async def write_fits(self, filename: str, hdulist: fits.HDUList, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            hdulist: hdu list to write.
        """

        # open file
        with self.open_file(filename, 'wb') as cache:
            with io.BytesIO() as bio:
                hdulist.writeto(bio, *args, **kwargs)
                cache.write(bio.getbuffer())

    async def read_image(self, filename: str) -> Image:
        """Convenience function that wraps around open_file() to read an Image.

        Args:
            filename: Name of file to download.

        Returns:
            An image object
        """
        with self.open_file(filename, 'rb') as f:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, f.read)
            return Image.from_bytes(data)

    async def write_image(self, filename: str, image: Image, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            image: Image to write.
        """

        # open file
        with self.open_file(filename, 'wb') as cache:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, partial(image.writeto, cache, *args, **kwargs))

    async def read_csv(self, filename: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
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
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, partial(pd.read_csv, f, *args, **kwargs))

        except pd.errors.EmptyDataError:
            # on error, return empty dataframe
            return pd.DataFrame()

    async def write_csv(self, df: pd.DataFrame, filename: str, *args: Any, **kwargs: Any) -> None:
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
                data = sio.getvalue().encode('utf8')

                # and write all content to file
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, partial(f.write, data, *args, **kwargs))

    async def read_yaml(self, filename: str) -> Dict[str, Any]:
        """Convenience function for reading a YAML file into a dict.

        Args:
            filename: Name of file to read.

        Returns:
            Content of file.
        """

        # open file
        with self.open_file(filename, 'r') as f:
            # read YAML
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, yaml.safe_load, cast(IO[bytes], f))
            return cast(Dict[str, Any], data)

    async def write_yaml(self, data: Dict[str, Any], filename: str) -> None:
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
                data = bytes(sio.getvalue(), 'utf8')

                # write file from StringIO
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, f.write, data)

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
