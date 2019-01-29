import os

import pytest

from pytel.vfs import VirtualFileSystem


def test_read_file():
    # create config
    roots = {
        'local': {
            'class': 'pytel.vfs.LocalFile',
            'root': os.path.dirname(__file__)
        }
    }

    # create vfs
    vfs = VirtualFileSystem(roots=roots)

    # open file
    filename = '/local/' + os.path.basename(__file__)
    with vfs.open_file(filename, 'r') as f:
        assert f.readline() == b'import os\n'
