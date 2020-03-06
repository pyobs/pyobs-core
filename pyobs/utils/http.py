# taken from: https://www.peterbe.com/plog/best-practice-with-retries-with-requests
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# disable warnings
# TODO: is there a better way? we can link to actual CA:
# https://urllib3.readthedocs.io/en/latest/user-guide.html#ssl
# but does that only work in Linux?
# some more:
# https://github.com/psf/requests/issues/2214
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
