import asyncio
import os
from typing import Optional, Any, AnyStr, List
import paramiko
import paramiko.sftp

from .file import VFSFile


class SSHFile(VFSFile):
    """VFS wrapper for a file that can be accessed over a SFTP connection."""

    __module__ = "pyobs.vfs"

    def __init__(
        self,
        name: str,
        mode: str = "r",
        bufsize: int = -1,
        hostname: Optional[str] = None,
        port: int = 22,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keyfile: Optional[str] = None,
        root: Optional[str] = None,
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
        self._full_path = os.path.join(root, name)

        # check
        if hostname is None:
            raise ValueError("No hostname given.")

        # connect
        self._ssh = paramiko.SSHClient()
        self._ssh.load_system_host_keys()
        self._ssh.connect(hostname, port=port, username=username, password=password, key_filename=keyfile)

        # need to create directory?
        if mkdir:
            path = os.path.dirname(self._full_path)
            self._ssh.exec_command(f"mkdir -p {path}")

        # build filename
        self.filename = name
        self.mode = mode
        self._buffer = b"" if "b" in self.mode else ""
        self._pos = 0
        self._open = True

    async def _download(self) -> None:
        """For read access, download the file into a local buffer.

        Raises:
            FileNotFoundError: If file could not be found.
        """

        _, stdout, stderr = self._ssh.exec_command(f"cat {self._full_path}")
        self._buffer = stdout.read()

    async def read(self, n: int = -1) -> AnyStr:
        """Read number of bytes from stream.

        Args:
            n: Number of bytes to read. Read until end, if -1.

        Returns:
            Read bytes.
        """

        # load file
        if len(self._buffer) == 0 and "r" in self.mode:
            await self._download()

        # check size
        if n == -1:
            data = self._buffer
            self._pos = len(self._buffer) - 1
        else:
            # extract data to read
            data = self._buffer[self._pos : self._pos + n]
            self._pos += n

        # return data
        return data

    async def write(self, s: AnyStr) -> None:
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        self._buffer += s

    async def close(self) -> None:
        """Close stream."""

        # write it?
        if "w" in self.mode and self._open:
            await self._upload()

        # set flag
        self._open = False

    async def _upload(self) -> None:
        """If in write mode, actually send the file to the SSH server."""

        transport = self._ssh.get_transport()
        with transport.open_channel(kind="session") as channel:
            channel.exec_command(f"cat > {self._full_path}")
            channel.sendall(self._buffer)

    @staticmethod
    async def listdir(path: str, **kwargs: Any) -> List[str]:
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

        p = os.path.join(kwargs["root"], path)
        _, stdout, stderr = ssh.exec_command(f"ls -1 {p}")
        files = stdout.readlines()

        # disconnect and return list
        ssh.close()
        return [f.strip() for f in files]


__all__ = ["SSHFile"]
