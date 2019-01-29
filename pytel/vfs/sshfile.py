from io import FileIO
import os
import paramiko
import paramiko.sftp


class SSHFile(paramiko.SFTPFile):
    def __init__(self, name, mode='r', bufsize=-1, hostname: str = None, port: int = 22, username: str = None,
                 password: str = None, keyfile: str = None, root: str = None, mkdir: str = None, *args, **kwargs):
        # no root given?
        if root is None:
            raise ValueError('No root directory given.')

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

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
        t, msg = self._sftp._request(paramiko.sftp.CMD_OPEN, full_path, imode, attrblock)
        if t != paramiko.sftp.CMD_HANDLE:
            raise paramiko.SFTPError('Expected handle')
        handle = msg.get_binary()

        # init FileIO
        paramiko.SFTPFile.__init__(self, self._sftp, handle, mode, bufsize)

    @classmethod
    def default_config(cls):
        cfg = super(SSHFile, cls).default_config()
        cfg['hostname'] = None
        cfg['port'] = 22
        cfg['username'] = None
        cfg['password'] = None
        cfg['keyfile'] = None
        cfg['root'] = None
        cfg['mkdir'] = True
        return cfg
