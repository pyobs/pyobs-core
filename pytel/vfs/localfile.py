from io import FileIO
import os


class LocalFile(FileIO):
    def __init__(self, name, mode='r', root: str = None, mkdir: bool = True, *args, **kwargs):
        # no root given?
        if root is None:
            raise ValueError('No root directory given.')

        # filename is not allowed to start with a / or contain ..
        if name.startswith('/') or '..' in name:
            raise ValueError('Only files within root directory are allowed.')

        # build filename
        self.filename = name
        full_path = os.path.join(root, name)

        # need to create directory?
        path = os.path.dirname(full_path)
        if not os.path.exists(path):
            if mkdir:
                os.makedirs(path)
            else:
                raise ValueError('Cannot write into sub-directory with disabled mkdir option.')

        # init FileIO
        FileIO.__init__(self, full_path, mode)
