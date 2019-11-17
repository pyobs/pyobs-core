import pytest

from pyobs.vfs import SSHFile


@pytest.mark.ssh
def test_write_read():
    # create config
    root = '/tmp'
    hostname = 'localhost'

    # write file
    with SSHFile('sshfile_test.txt', 'w', root=root, hostname=hostname) as f:
        f.write('Hello world!')

    # read file
    with SSHFile('sshfile_test.txt', 'r', root=root, hostname=hostname) as f:
        assert f.read() == b'Hello world!'
