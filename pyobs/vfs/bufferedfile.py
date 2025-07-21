from abc import ABCMeta

from pyobs.vfs import VFSFile


class BufferedFile(VFSFile, metaclass=ABCMeta):
    """Base class for all byffered VFS file classes."""

    __module__ = "pyobs.vfs"

    """Global buffer."""
    _bufferedFiles: dict[str, str | bytes] = {}

    def _buffer_exists(self, filename: str) -> bool:
        return filename in self._bufferedFiles

    def _clear_buffer(self, filename: str) -> None:
        if filename in self._bufferedFiles:
            del self._bufferedFiles[filename]

    def _set_buffer(self, filename: str, s: str | bytes) -> None:
        self._bufferedFiles[filename] = s

    def _append_to_buffer(self, filename: str, s: str | bytes) -> None:
        if not self._buffer_exists(filename):
            self._set_buffer(filename, s)
        else:
            buf = self._bufferedFiles[filename]
            if isinstance(buf, str) and isinstance(s, str):
                self._bufferedFiles[filename] = buf + s
            elif isinstance(buf, bytes) and isinstance(s, bytes):
                self._bufferedFiles[filename] = buf + s
            else:
                raise TypeError("Cannot concatenate str and bytes.")

    def _buffer(self, filename: str) -> str | bytes:
        if not self._buffer_exists(filename):
            raise IndexError("File not found.")
        return self._bufferedFiles[filename]


__all__ = ["BufferedFile"]
