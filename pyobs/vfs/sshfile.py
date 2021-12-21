import os
from typing import Optional, Any

import paramiko
import paramiko.sftp

from .file import VFSFile


class SSHFile(VFSFile, paramiko.SFTPFile):
    """VFS wrapper for a file that can be accessed over a SFTP connection."""
    __module__ = 'pyobs.vfs'

    def __init__(self, name: str, mode: str = 'r', bufsize: int = -1, hostname: Optional[str] = None, port: int = 22,
                 username: Optional[str] = None, password: Optional[str] = None, keyfile: Optional[str] = None,
                 root: Optional[str] = None, mkdir: bool = True, **kwargs: Any):
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
            raise ValueError('No root directory given.')

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

        # check
        if hostname is None:
            raise ValueError('No hostname given.')

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
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # just the code from paramiko.SFTPClient.open
        imode = 0
        if ('r' in mode) or ('+' in mode):
            imode |= paramiko.sftp.SFTP_FLAG_READ
        if ('w' in mode) or ('+' in mode) or ('a' in mode):
            imode |= paramiko.sftp.SFTP_FLAG_WRITE
        if 'w' in mode:
            imode |= paramiko.sftp.SFTP_FLAG_CREATE | paramiko.sftp.SFTP_FLAG_TRUNC
        if 'a' in mode:
            imode |= paramiko.sftp.SFTP_FLAG_CREATE | paramiko.sftp.SFTP_FLAG_APPEND
        if 'x' in mode:
            imode |= paramiko.sftp.SFTP_FLAG_CREATE | paramiko.sftp.SFTP_FLAG_EXCL
        attrblock = paramiko.SFTPAttributes()
        t, msg = self._sftp._request(paramiko.sftp.CMD_OPEN, full_path, imode, attrblock)  # type: ignore
        if t != paramiko.sftp.CMD_HANDLE:
            raise paramiko.SFTPError('Expected handle')
        handle = msg.get_binary()

        # init FileIO
        paramiko.SFTPFile.__init__(self, self._sftp, handle, mode, bufsize)


__all__ = ['SSHFile']
