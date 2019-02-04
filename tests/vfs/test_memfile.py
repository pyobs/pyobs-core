from pytel.vfs import MemoryFile


def test_memfile():
    with MemoryFile('test.txt', 'w') as f:
        f.write(b'Hello world!')

    with MemoryFile('test.txt', 'r') as f:
        assert b'Hello world!' == f.read()
