import io
from typing import List, Dict
import requests
import urllib.parse
import logging

from pyobs.utils.time import Time
from pyobs.images import Image
from .archive import Archive, FrameInfo
from ..enums import ImageType

log = logging.getLogger(__name__)


class PyobsArchiveFrameInfo(FrameInfo):
    """Frame info for pyobs archive."""
    def __init__(self, info: dict, *args, **kwargs):
        self.info = info

    @property
    def id(self):
        return self.info['id']

    @property
    def filename(self):
        return self.info['basename']

    @property
    def url(self):
        return self.info['url']

    @property
    def dateobs(self):
        return Time(self.info['DATE_OBS'])

    @property
    def filter_name(self):
        return self.info['FILTER']

    @property
    def binning(self):
        return int(self.info['binning'][0])


class PyobsArchive(Archive):
    """Connector class to running pyobs-archive instance."""
    __module__ = 'pyobs.utils.archive'

    def __init__(self, url: str, token: str, proxies: dict = None, *args, **kwargs):
        self._url = url
        self._headers = {'Authorization': 'Token ' + token}
        self._proxies = proxies

    def list_options(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None):
        # build URL
        url = urllib.parse.urljoin(self._url, 'frames/aggregate/')

        # and params
        params = self._build_query(start, end, night, site, telescope, instrument, image_type, binning,
                                   filter_name, rlevel)

        # do request
        r = requests.get(url, params=params, headers=self._headers, proxies=self._proxies)
        if r.status_code != 200:
            raise ValueError('Could not query frames')

        # create frames and return them
        return r.json()

    def list_frames(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None) \
            -> List[PyobsArchiveFrameInfo]:
        # build URL
        url = urllib.parse.urljoin(self._url, 'frames/')

        # and params
        params = self._build_query(start, end, night, site, telescope, instrument, image_type, binning,
                                   filter_name, rlevel)

        # set offset and limit
        # TODO: instead of setting large limit, request multiple pages, if necessary
        params['offset'] = 0
        params['limit'] = 10000

        # do request
        r = requests.get(url, params=params, headers=self._headers, proxies=self._proxies)
        if r.status_code != 200:
            raise ValueError('Could not query frames')

        # create frames and return them
        return [PyobsArchiveFrameInfo(frame, archive=self) for frame in r.json()['results']]

    def _build_query(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None):
        # build params
        params = {}
        if start is not None:
            params['start'] = start.isot
        if end is not None:
            params['end'] = end.isot
        if night is not None:
            params['night'] = night
        if site is not None:
            params['SITE'] = site
        if telescope is not None:
            params['TELESCOPE'] = telescope
        if instrument is not None:
            params['INSTRUMENT'] = instrument
        if image_type is not None:
            params['IMAGETYPE'] = image_type.value
        if binning is not None:
            params['binning'] = binning
        if filter_name is not None:
            params['FILTER'] = filter_name
        if rlevel is not None:
            params['RLEVEL'] = rlevel
        return params

    def download_frames(self, infos: List[PyobsArchiveFrameInfo]) -> List[Image]:
        # loop infos
        images = []
        for info in infos:
            # download
            url = urllib.parse.urljoin(self._url, info.url)
            r = requests.get(url, headers=self._headers, proxies=self._proxies)

            # create image
            try:
                image = Image.from_bytes(r.content)
                images.append(image)
            except OSError:
                log.exception('Error downloading file %s.', info.filename)

        # return all
        return images

    def download_headers(self, infos: List[PyobsArchiveFrameInfo]) -> List[Dict]:
        # loop infos
        headers = []
        for info in infos:
            # download
            url = urllib.parse.urljoin(self._url, info.url).replace('download', 'headers')
            r = requests.get(url, headers=self._headers, proxies=self._proxies)

            try:
                results = r.json()['results']
                headers.append(dict((d['key'], d['value']) for d in results))
            except KeyError:
                log.error('Could not fetch headers for %s.', info.filename)
                headers.append({})

        # return all
        return headers

    def upload_frames(self, images: List[Image]):
        # build URL
        url = urllib.parse.urljoin(self._url, 'frames/create/')

        # create session
        session = requests.session()

        # do some initial GET request for getting the csrftoken
        session.get(self._url, headers=self._headers, proxies=self._proxies)

        # define list of files and url
        files = {}
        for img in images:
            # get filename
            filename = img.header['FNAME']

            # write HDU to BytesIO
            with io.BytesIO() as bio:
                # write it
                img.writeto(bio)

                # get data
                files[filename] = bio.getvalue()

        # post it
        r = session.post(url, data={'csrfmiddlewaretoken': session.cookies['csrftoken']},
                         files=files, headers=self._headers, proxies=self._proxies)

        # success, if status code is 200
        if r.status_code != 200:
            raise ValueError('Cannot write file, received status_code %d.' % r.status_code)

        # check json
        json = r.json()
        if 'created' not in json or json['created'] == 0:
            if 'errors' in json:
                raise ValueError('Could not create file in archive: ' + str(json['errors']))
            else:
                raise ValueError('Could not create file in archive.')


__all__ = ['PyobsArchiveFrameInfo', 'PyobsArchive']
