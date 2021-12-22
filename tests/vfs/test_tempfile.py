import os

from pyobs.vfs import TempFile

'''
def test_write_file():
    # create new temp file with name
    with TempFile(mode='w') as f:
        # does file exist?
        assert os.path.exists(f.name)

    # file should be gone
    assert not os.path.exists(f.name)


def test_name():
    # test prefix
    with TempFile(mode='w', prefix='test') as f:
        assert f.filename.startswith('test')

    # test suffix
    with TempFile(mode='w', suffix='.fits') as f:
        assert f.filename.endswith('.fits')

    # test given name
    with TempFile(name='test.txt', mode='w') as f:
        assert f.filename == 'test.txt'
'''
