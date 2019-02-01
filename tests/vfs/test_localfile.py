import os
import pytest

from pytel.vfs import LocalFile


def test_read_file():
    # create config
    root = os.path.dirname(__file__)

    # open file
    filename = os.path.basename(__file__)
    with LocalFile(filename, 'r', root=root) as f:
        assert f.readline() == b'import os' + bytes(os.linesep, 'utf-8')


def test_file_not_found():
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(FileNotFoundError):
        with LocalFile('doesnt_exist.txt', 'r', root=root) as f:
            pass


def test_invalid_path():
    # create config
    root = os.path.dirname(__file__)

    # open file
    with pytest.raises(ValueError):
        with LocalFile('../test.txt', 'r', root=root) as f:
            pass

    # open file
    with pytest.raises(ValueError):
        with LocalFile('/test.txt', 'r', root=root) as f:
            pass


def test_write_file(tmpdir):
    # create config
    root = str(tmpdir)

    # open file for write
    with LocalFile('test.txt', 'w', root=root) as f:
        f.write(b'This is a test')

    # test it
    assert tmpdir.join('test.txt').read() == 'This is a test'


def test_create_dir(tmpdir):
    # create config
    root = str(tmpdir)

    # open file for write
    with LocalFile('sub/test.txt', 'w', root=root) as f:
        f.write(b'This is a test')

    # test it
    assert tmpdir.join('sub/test.txt').read() == 'This is a test'

    # this should throw an exception
    with pytest.raises(ValueError):
        with LocalFile('sub2/test.txt', 'w', root=root, mkdir=False) as f:
            f.write(b'This is a test')

