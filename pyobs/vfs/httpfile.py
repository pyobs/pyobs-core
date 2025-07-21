import io
import uuid
from typing import Any
from urllib.parse import urljoin
import logging
import aiohttp

from .bufferedfile import BufferedFile


log = logging.getLogger(__name__)


class HttpFile(BufferedFile):
    """Wraps a file on a HTTP server that can be accessed via GET/POST.
    Especially useful in combination with :class:`~pyobs.modules.utils.HttpFileCache`."""

    __module__ = "pyobs.vfs"

    def __init__(
        self,
        name: str,
        mode: str = "r",
        download: str | None = None,
        upload: str | None = None,
        username: str | None = None,
        password: str | None = None,
        verify_tls: bool = False,
        timeout: int = 30,
        **kwargs: Any,
    ):
        """Creates a new HTTP file.

        Args:
            name: Name of file.
            mode: Open mode (r/w).
            download: Base URL for downloading files. If None, no read access possible.
            upload: Base URL for uploading files. If None, no write access possible.
            username: Username for accessing the HTTP server.
            password: Password for accessing the HTTP server.
            verify_tls: Whether to verify TLS certificates.
            timeout: Timeout in seconds for uploading/downloading files.
        """

        # init
        io.RawIOBase.__init__(self)
        self._verify_tls = verify_tls
        self._timeout = timeout

        # auth
        self._auth = None
        if username is not None and password is not None:
            self._auth = aiohttp.BasicAuth(username, password)

        # filename is not allowed to start with a / or contain ..
        if name.startswith("/") or ".." in name:
            raise ValueError("Only files within root directory are allowed.")

        # build filename
        self.filename = name
        self.mode = mode
        self._pos = 0
        self._open = True

        # URLs given?
        self._download_path = download
        self._upload_path = upload
        if "r" in self.mode and self._download_path is None:
            raise ValueError("No download URL given.")
        if "w" in self.mode and self._upload_path is None:
            raise ValueError("No upload URL given.")

    @property
    def url(self) -> str:
        """Returns URL of file."""
        if self._download_path is None:
            raise ValueError("No download URL given.")
        return urljoin(self._download_path, self.filename)

    async def _download(self) -> None:
        """For read access, download the file into a local buffer.

        Raises:
            FileNotFoundError: If file could not be found.
        """

        # do request
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, auth=self._auth, timeout=self._timeout) as response:
                # check response
                if response.status == 200:
                    # get data and return it
                    self._set_buffer(self.filename, await response.read())
                elif response.status == 401:
                    log.error("Wrong credentials for downloading file.")
                    raise FileNotFoundError
                else:
                    log.error("Could not download file from filecache.")
                    raise FileNotFoundError

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
            s: Bytes of data to write.
        """
        self._append_to_buffer(self.url, s)

    async def close(self) -> None:
        """Close stream."""

        # write it?
        if "w" in self.mode and self._open:
            await self._upload()

        # set flag
        self._open = False

    async def _upload(self) -> None:
        """If in write mode, actually send the file to the HTTP server."""

        # filename given?
        filename = str(uuid.uuid4()) if self.filename is None else self.filename

        # check
        if self._upload_path is None:
            raise ValueError("No upload URL given.")

        # send data and return image ID
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("file", self._buffer(filename), filename=filename)
            async with session.post(self._upload_path, auth=self._auth, data=data, timeout=self._timeout) as response:
                if response.status == 401:
                    log.error("Wrong credentials for uploading file.")
                    raise FileNotFoundError
                elif response.status != 200:
                    log.error(f"Could not upload file to filecache: {response.status} {response.reason}")
                    raise FileNotFoundError


__all__ = ["HttpFile"]
