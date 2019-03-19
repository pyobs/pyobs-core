import io
import tarfile
import os

from pyobs.vfs.tarfile import TarFile


class MonkeyVFS:
    def open_file(self, *args, **kwargs):
        return open(*args, **kwargs)


class MonkeyApp:
    @property
    def vfs(self):
        return MonkeyVFS()


def test_tarfile(monkeypatch):
    # vfs
    vfs = MonkeyVFS()

    # create config
    source = {'class': 'pyobs.vfs.filelists.TestingFileList'}

    # open file
    with io.BytesIO() as bio:
        with TarFile('test.tar', 'rb', source=source, vfs=vfs) as f:
            bio.write(f.read())
        zip_data = bio.getvalue()

    # try to unzip it
    with io.BytesIO(zip_data) as bio:
        with tarfile.open(fileobj=bio) as tar:
            # check list of files
            assert tar.getnames() == ['testing.py']

            # extract file
            fd = tar.extractfile('testing.py')
            assert fd.readline() == b'import logging' + bytes(os.linesep, 'utf-8')
