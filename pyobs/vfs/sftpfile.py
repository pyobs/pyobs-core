import asyncio
import os
from typing import Any
import paramiko
import paramiko.sftp

from .file import VFSFile


class SFTPFile(VFSFile):
    """VFS wrapper for a file that can be accessed over a SFTP connection."""

    __module__ = "pyobs.vfs"

    def __init__(
        self,
        name: str,
        mode: str = "r",
        hostname: str | None = None,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        keyfile: str | None = None,
        root: str | None = None,
        mkdir: bool = True,
        **kwargs: Any,
    ):
        """Open/create a file over a SSH connection.

        Args:
            name: Name of file.
            mode: Open mode.
            bufsize: Size of buffer size for SFTP connection.
            hostname: Name of host to connect to.
            port: Port on host to connect to.
            username: Username to log in on host.
            password: Password for username.
            keyfile: Path to SSH key on local machine.
            root: Root directory on host.
            mkdir: Whether or not to automatically create directories.
        """

        # no root given?
        if root is None:
            raise ValueError("No root directory given.")

        # filename is not allowed to start with a / or contain ..
        if name.startswith("/") or ".." in name:
            raise ValueError("Only files within root directory are allowed.")

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

        # check
        if hostname is None:
            raise ValueError("No hostname given.")

        # connect
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.connect(hostname, port=port, username=username, password=password, key_filename=keyfile)
        self._sftp = self._ssh.open_sftp()

        # need to create directory?
        path = os.path.dirname(full_path)
        try:
            self._sftp.chdir(path)
        except IOError:
            if mkdir:
                self._sftp.mkdir(path)
            else:
                raise ValueError("Cannot write into sub-directory with disabled mkdir option.")

        # open file
        self._fd = self._sftp.file(full_path, mode)

    async def close(self) -> None:
        """Close file."""
        self._sftp.close()
        self._ssh.close()

    async def read(self, n: int = -1) -> str | bytes:
        return self._fd.read(n)

    async def write(self, s: str | bytes) -> None:
        self._fd.write(s)

    @staticmethod
    async def listdir(path: str, **kwargs: Any) -> list[str]:
        """Returns content of given path.

        Args:
            path: Path to list.
            kwargs: Parameters for specific file implementation (same as __init__).

        Returns:
            List of files in path.
        """

        # connect
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.connect(
            kwargs["hostname"],
            port=kwargs["port"] if "port" in kwargs else 22,
            username=kwargs["username"],
            password=kwargs["password"] if "password" in kwargs else None,
            key_filename=kwargs["keyfile"] if "keyfile" in kwargs else None,
        )
        sftp = ssh.open_sftp()

        # list files in path
        loop = asyncio.get_running_loop()
        files = await loop.run_in_executor(None, sftp.listdir, os.path.join(kwargs["root"], path))

        # disconnect and return list
        sftp.close()
        ssh.close()
        return files


__all__ = ["SFTPFile"]
