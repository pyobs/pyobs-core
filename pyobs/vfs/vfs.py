import io
import logging
import os
from typing import Optional, Dict, Any, Tuple, List, Callable
import yaml
from astropy.io import fits
import pandas as pd

from pyobs.object import get_class_from_string
from pyobs.images import Image
from .file import VFSFile


log = logging.getLogger(__name__)


class VirtualFileSystem(object):
    """Base for a virtual file system."""

    __module__ = "pyobs.vfs"

    def __init__(self, roots: Optional[Dict[str, Any]] = None, **kwargs: Any):
        """Create a new VFS.

        Args:
            roots: Dictionary containing roots, see :mod:`~pyobs.vfs` for examples.
        """

        # if no root for 'pyobs' is given, add one
        self._roots: Dict[str, Any] = {
            "pyobs": {"class": "pyobs.vfs.LocalFile", "root": os.path.expanduser("~/.pyobs/")}
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
        if path.startswith("/"):
            path = path[1:]

        # no more slash left?
        if "/" not in path:
            raise ValueError("No valid path with a root.")

        # get position of first slash and split
        pos = path.index("/")
        root = path[:pos]
        filename = path[pos + 1 :]

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
            raise ValueError("Could not find root {0} for file.".format(root))

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
        async with self.open_file(filename, "rb") as f:
            data = await f.read()
            return fits.HDUList.fromstring(data)

    async def write_fits(self, filename: str, hdulist: fits.HDUList, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            hdulist: hdu list to write.
        """

        # open file
        async with self.open_file(filename, "wb") as f:
            with io.BytesIO() as bio:
                hdulist.writeto(bio, *args, **kwargs)
                await f.write(bio.getvalue())

    async def read_image(self, filename: str) -> Image:
        """Convenience function that wraps around open_file() to read an Image.

        Args:
            filename: Name of file to download.

        Returns:
            An image object
        """
        async with self.open_file(filename, "rb") as f:
            data = await f.read()
            return Image.from_bytes(data)

    async def write_image(self, filename: str, image: Image, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing an Image to a FITS file.

        Args:
            filename: Name of file to write.
            image: Image to write.
        """

        # open file
        async with self.open_file(filename, "wb") as f:
            with io.BytesIO() as bio:
                image.writeto(bio, *args, **kwargs)
                await f.write(bio.getvalue())

    async def read_csv(self, filename: str, *args: Any, **kwargs: Any) -> pd.DataFrame:
        """Convenience function for reading a CSV file into a DataFrame.

        Args:
            filename: Name of file to read.

        Returns:
            DataFrame with content of file.
        """

        try:
            # open file
            async with self.open_file(filename, "r") as f:
                data = await f.read()
                return pd.read_csv(io.StringIO(data), *args, **kwargs)

        except pd.errors.EmptyDataError:
            # on error, return empty dataframe
            return pd.DataFrame()

    async def write_csv(self, filename: str, df: pd.DataFrame, *args: Any, **kwargs: Any) -> None:
        """Convenience function for writing a CSV file from a DataFrame.

        Args:
            filename: Name of file to write.
            df: DataFrame to write.
        """

        async with self.open_file(filename, "w") as f:
            # create a StringIO as temporary write target
            with io.StringIO() as sio:
                # write table to sio
                df.to_csv(sio, *args, **kwargs)

                # and write all content to file
                await f.write(sio.getvalue())

    async def read_yaml(self, filename: str) -> Any:
        """Convenience function for reading a YAML file into a dict.

        Args:
            filename: Name of file to read.

        Returns:
            Content of file.
        """

        # open file
        async with self.open_file(filename, "r") as f:
            # read YAML
            data = await f.read()
            return yaml.safe_load(io.StringIO(data))

    async def write_yaml(self, filename: str, data: Any) -> None:
        """Convenience function for writing a YAML file from a dict.

        Args:
            data: dict to write.
            filename: Name of file to write.
        """

        # open file
        async with self.open_file(filename, "w") as f:
            # create StringIO as temp storage
            with io.StringIO() as sio:
                # dump to StringIO
                yaml.dump(data, sio)

                # write file from StringIO
                await f.write(sio.getvalue())

    def _get_method(self, path: str, method: str) -> Tuple[Callable[..., Any], str, str]:
        # split root
        if not path.endswith("/"):
            path += "/"
        root, path = VirtualFileSystem.split_root(path)

        # get root class
        klass = get_class_from_string(self._roots[root]["class"])

        # get find method
        return getattr(klass, method), root, path

    def find(self, path: str, pattern: str) -> List[str]:
        """Find a file in the given path.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.

        Returns:
            List of found files.
        """

        # get method
        find, root, path = self._get_method(path, "find")

        # and call it
        return find(path, pattern, **self._roots[root])

    def listdir(self, path: str) -> List[str]:
        """Find a file in the given path.

        Args:
            path: Path to search in.
            pattern: Pattern to search for.

        Returns:
            List of found files.
        """

        # get method
        listdir, root, path = self._get_method(path, "listdir")

        # and call it
        return listdir(path, **self._roots[root])

    def exists(self, path: str) -> bool:
        """Checks, whether a given path or file exists.

        Args:
            path: Path to check.

        Returns:
            Whether it exists or not
        """

        # get method
        exists, root, path = self._get_method(path, "exists")

        # and call it
        return exists(path, **self._roots[root])


__all__ = ["VirtualFileSystem", "VFSFile"]
