import io
import tarfile

from pytel import Application
from pytel.vfs.tarfile import TarFile


class MonkeyVFS:
    def open_file(self, *args, **kwargs):
        return open(*args, **kwargs)


class MonkeyApp:
    @property
    def vfs(self):
        return MonkeyVFS()


def test_tarfile(monkeypatch):
    # monkey patch
    monkeypatch.setattr(Application, 'instance', lambda: MonkeyApp())

    # create config
    source = {'class': 'pytel.vfs.filelists.TestingFileList'}

    # open file
    with io.BytesIO() as bio:
        with TarFile('test.tar', 'rb', source=source) as f:
            bio.write(f.read())
        zip_data = bio.getvalue()

    # try to unzip it
    with io.BytesIO(zip_data) as bio:
        with tarfile.open(fileobj=bio) as tar:
            # check list of files
            assert tar.getnames() == ['testing.py']

            # extract file
            fd = tar.extractfile('testing.py')
            assert fd.readline() == b'import io\n'
