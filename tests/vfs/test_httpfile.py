import requests

from pytel.vfs import HttpFile


class Response:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


def test_upload_download(monkeypatch):
    # mock it
    uploaded = None
    def requests_get(url, params=None, **kwargs):
        global uploaded
        return Response(200, uploaded)
    def requests_post(url, data=None, json=None, **kwargs):
        global uploaded
        uploaded = data
        return Response(200, None)
    monkeypatch.setattr(requests, 'get', requests_get)
    monkeypatch.setattr(requests, 'post', requests_post)

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
