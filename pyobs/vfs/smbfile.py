import asyncio
from functools import partial
from pathlib import PureWindowsPath
from typing import Optional, Any, AnyStr, List
import logging

from .file import VFSFile


# set logging for smbprotocol package
logging.getLogger("smbprotocol").setLevel(logging.WARNING)


class SMBFile(VFSFile):
    """VFS wrapper for a file that can be accessed over a SMB connection.

    Requires smbprotocol package to work.
    """

    __module__ = "pyobs.vfs"

    def __init__(
        self,
        name: str,
        mode: str = "r",
        hostname: Optional[str] = None,
        share: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        root: Optional[str] = None,
        mkdir: bool = True,
        **kwargs: Any,
    ):
        """Open/create a file over a SSH connection.

        Args:
            name: Name of file.
            mode: Open mode.
            hostname: Name of host to connect to.
            share: Share to access on server.
            username: Username to log in on host.
            password: Password for username.
            keyfile: Path to SSH key on local machine.
            root: Root directory on host.
            mkdir: Whether or not to automatically create directories.
        """
        try:
            import smbclient  # type: ignore
        except ModuleNotFoundError:
            raise ValueError("Module smbprotocol not found, please install package.")

        # no root given?
        if root is None:
            raise ValueError("No root directory given.")

        # filename is not allowed to start with a / or contain ..
        if name.startswith("/") or ".." in name:
            raise ValueError("Only files within root directory are allowed.")

        # check
        if hostname is None or share is None:
            raise ValueError("No hostname/share given.")

        # store connection details
        self._hostname = hostname
        self._share = share
        self._username = username
        self._password = password

        # build filename
        self.filename = name
        self._full_path = PureWindowsPath(rf"\\{hostname}\{share}\\") / root / name

        # need to create directory?
        path = str(self._full_path.parent)
        try:
            smbclient.lstat(path)
        except IOError:
            if mkdir:
                smbclient.mkdir(path)
            else:
                raise ValueError("Cannot write into sub-directory with disabled mkdir option.")

        # open file
        self._fd = smbclient.open_file(
            str(self._full_path), mode=mode, username=self._username, password=self._password
        )

    async def close(self) -> None:
        """Close file."""
        self._fd.close()

    async def read(self, n: int = -1) -> AnyStr:
        return self._fd.read(n)

    async def write(self, s: AnyStr) -> None:
        self._fd.write(s)

    @staticmethod
    async def listdir(path: str, **kwargs: Any) -> List[str]:
        """Returns content of given path.

        Args:
            path: Path to list.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            List of files in path.
        """
        import smbclient

        # get settings
        hostname = kwargs["hostname"]
        share = kwargs["share"]
        username = kwargs["username"]
        password = kwargs["password"]
        root = kwargs["root"]

        # get path and return list
        network = PureWindowsPath(rf"\\{hostname}\{share}\\") / root / path
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(smbclient.listdir, str(network), username=username, password=password)
        )


__all__ = ["SMBFile"]
