"""
import time

from pyobs.vfs import VirtualFileSystem
from pyobs.comm.dummy import DummyComm
from pyobs.modules.image import NewImageWriter
from pyobs.events import NewImageEvent


def test_newimage():
    # we need a VFS and Comm
    vfs = VirtualFileSystem(roots={'input': {'class': 'pyobs.vfs.TempFile'},
                                   'output': {'class': 'pyobs.vfs.MemoryFile'}})
    comm = DummyComm()

    # create NewImageWriter
    niw = NewImageWriter(vfs=vfs, comm=comm, root='/output')
    niw.open()

    # create temp file
    with vfs.open_file('/input/test.txt', 'w') as fin:
        # write something in it
        fin.write(b'Hello world')

        # create event
        event = NewImageEvent('/input/test.txt')

        # send event and wait a little
        assert niw.process_new_image_event(event, 'dummy') is True
        time.sleep(1)

        # open output
        with vfs.open_file('/output/test.txt', 'r') as fout:
            assert b'Hello world' == fout.read()

    # close writer
    niw.close()
"""
