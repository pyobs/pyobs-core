import os
from typing import Any
import paramiko
import paramiko.sftp

from .bufferedfile import BufferedFile


class SSHFile(BufferedFile):
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
        BufferedFile.__init__(self)

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
        self._pos = 0
        self._open = True

        # clear cache on write?
        if "w" in self.mode:
            self._clear_buffer(self.filename)

    async def _download(self) -> None:
        """For read access, download the file into a local buffer.

        Raises:
            FileNotFoundError: If file could not be found.
        """

        _, stdout, stderr = self._ssh.exec_command(f"cat {self._full_path}")
        self._set_buffer(self.filename, stdout.read())

    async def read(self, n: int = -1) -> str | bytes:
        """Read number of bytes from stream.

        Args:
            n: Number of bytes to read. Read until end, if -1.

        Returns:
            Read bytes.
        """

        # get buffer
        if not self._buffer_exists(self.filename):
            raise IndexError("File not found.")
        buf = self._buffer(self.filename)

        # load file
        if len(buf) == 0 and "r" in self.mode:
            await self._download()

        # check size
        if n == -1:
            data = buf
            self._pos = len(buf) - 1
        else:
            # extract data to read
            data = buf[self._pos : self._pos + n]
            self._pos += n

        # return data
        return data

    async def write(self, s: str | bytes) -> None:
        """Write data into the stream.

        Args:
            b: Bytes of data to write.
        """
        self._append_to_buffer(self.filename, s)

    async def close(self) -> None:
        """Close stream."""

        # write it?
        if "w" in self.mode and self._open:
            await self._upload()

        # clear buffer
        self._clear_buffer(self.filename)

        # set flag
        self._open = False
        self._ssh.close()

    async def _upload(self) -> None:
        """If in write mode, actually send the file to the SSH server."""

        transport = self._ssh.get_transport()
        if transport is None:
            raise OSError("Transport not available.")
        with transport.open_channel(kind="session") as channel:
            channel.exec_command(f"cat > {self._full_path}")
            buf = self._buffer(self.filename)
            if not isinstance(buf, bytes):
                buf = buf.encode()
            channel.sendall(buf)

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

        p = os.path.join(kwargs["root"], path)
        _, stdout, stderr = ssh.exec_command(f"ls -1 {p}")
        files = stdout.readlines()

        # disconnect and return list
        ssh.close()
        return [f.strip() for f in files]


__all__ = ["SSHFile"]
