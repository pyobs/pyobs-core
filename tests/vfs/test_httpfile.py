import requests

from pyobs.vfs import HttpFile


"""
class Response:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


uploaded = None


class Session:
    def mount(self, *args, **kwargs):
        pass

    def get(self, url, params=None, **kwargs):
        global uploaded
        return Response(200, uploaded)

    def post(self, url, data=None, json=None, **kwargs):
        global uploaded
        uploaded = data
        return Response(200, None)


def test_upload_download(monkeypatch):
    # mock it
    global uploaded
    monkeypatch.setattr(requests, 'Session', lambda: Session())

    # create config
    upload = 'http://localhost:37075/'
    download = 'http://localhost:37075/'

    # test data
    test = b'Hello world'

    # write file
    with HttpFile('test.txt', 'w', upload=upload, download=download) as f:
        f.write(test)

    # read data
    with HttpFile('test.txt', 'r', upload=upload, download=download) as f:
        assert test == f.read()
"""
