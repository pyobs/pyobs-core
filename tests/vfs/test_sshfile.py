import pytest

from pyobs.vfs import SSHFile


@pytest.mark.asyncio
@pytest.mark.ssh
async def test_write_read():
    # create config
    root = "/tmp"
    hostname = "localhost"

    # write file
    async with SSHFile("sshfile_test.txt", "w", root=root, hostname=hostname) as f:
        await f.write("Hello world!")

    # read file
    async with SSHFile("sshfile_test.txt", "r", root=root, hostname=hostname) as f:
        assert f.read() == b"Hello world!"
