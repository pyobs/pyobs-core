import time
import requests

from pytel import PytelModule
from pytel.modules.filecache import HttpFileCacheServer


def test_upload_download():
    # create server
    server = HttpFileCacheServer(port=54321)
    server.open()

    # wait for server to start listening
    for i in range(5):
        if server.opened:
            break
        time.sleep(1)
    assert server.opened is True

    # upload file via content-disposition
    headers = {
        'Content-Disposition': 'attachment; filename="test.txt"'
    }
    requests.post('http://localhost:37075/', b'Hello world', headers=headers)

    # download file
    res = requests.get('http://localhost:37075/test.txt')
    assert(res.content == b'Hello world')

    # upload file via url
    requests.post('http://localhost:37075/test2.txt', b'pytel is great')

    # download file
    res = requests.get('http://localhost:37075/test2.txt')
    assert (res.content == b'pytel is great')

    # uploading without filename should fail
    res = requests.post('http://localhost:37075/', b'So bad')
    assert res.status_code == 404

    # downloading with empty or unknown filename as well
    res = requests.get('http://localhost:37075/')
    assert res.status_code == 404
    res = requests.get('http://localhost:37075/notexisting.txt')
    assert res.status_code == 404

    # close app
    server.close()
