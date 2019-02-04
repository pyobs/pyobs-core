import os
from io import FileIO
from tempfile import NamedTemporaryFile
import logging


log = logging.getLogger(__name__)


class TempFile(FileIO):
    def __init__(self, name=None, mode='r', prefix=None, suffix=None, root: str = '/tmp/pytel/', mkdir: bool = True,
                 *args, **kwargs):
        # no root given?
        if root is None:
            raise ValueError('No root directory given.')

        # create root?
        if not os.path.exists(root):
            os.makedirs(root)

        # no filename?
        if name is None:
            # cannot read from non-existing filename
            if 'r' in mode:
                raise ValueError('No filename given to read from.')

            # create new temp file name
            with NamedTemporaryFile(mode=mode, prefix=prefix, suffix=suffix, dir=root) as tmp:
                name = os.path.basename(tmp.name)

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_name = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(full_name)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # init FileIO
        FileIO.__init__(self, full_name, mode)

    def close(self):
        # close file
        FileIO.close(self)

        # remove file
        if 'w' in self.mode:
            os.remove(self.name)
