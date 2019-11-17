import io
from typing import List
import requests
import urllib.parse

from pyobs.interfaces import ICamera
from pyobs.utils.time import Time
from pyobs.utils.images import Image
from .archive import Archive, FrameInfo


class PyobsArchiveFrameInfo(FrameInfo):
    def __init__(self, info: dict, *args, **kwargs):
        self.info = info

    @property
    def id(self):
        return self.info['id']

    @property
    def filename(self):
        return self.info['basename']

    @property
    def dateobs(self):
        return Time(self.info['DATE_OBS'])


class PyobsArchive(Archive):
    def __init__(self, url: str, token: str, *args, **kwargs):
        self._url = url
        self._headers = {'Authorization': 'Token ' + token}

    def list_options(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ICamera.ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None):
        # build URL
        url = urllib.parse.urljoin(self._url, '/api/frames/aggregate/')

        # and params
        params = self._build_query(start, end, night, site, telescope, instrument, image_type, binning,
                                   filter_name, rlevel)

        # do request
        r = requests.get(url, params=params, headers=self._headers)
        if r.status_code != 200:
            raise ValueError('Could not query frames')

        # create frames and return them
        return r.json()

    def list_frames(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ICamera.ImageType = None, binning: str = None, filter_name: str = None,
                    rlevel: int = None) \
            -> List[PyobsArchiveFrameInfo]:
        # build URL
        url = urllib.parse.urljoin(self._url, '/api/frames/')

        # and params
        params = self._build_query(start, end, night, site, telescope, instrument, image_type, binning,
                                   filter_name, rlevel)
        params['offset'] = 0
        params['limit'] = 1000

        # do request
        r = requests.get(url, params=params, headers=self._headers)
        if r.status_code != 200:
            raise ValueError('Could not query frames')

        # create frames and return them
        return [PyobsArchiveFrameInfo(frame, archive=self) for frame in r.json()['results']]

    def _build_query(self, start: Time = None, end: Time = None, night: str = None,
                    site: str = None, telescope: str = None, instrument: str = None,
                    image_type: ICamera.ImageType = None, binning: str = None, filter_name: str = None,
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
            # build URL
            url = urllib.parse.urljoin(self._url, '/api/frames/%d/download/' % info.id)

            # download
            r = requests.get(url, headers=self._headers)

            # create image
            image = Image.from_bytes(r.content)
            images.append(image)

        # return all
        return images

    def upload_frames(self, images: List[Image]):
        # build URL
        url = urllib.parse.urljoin(self._url, '/api/frames/create/')

        # create session
        session = requests.session()

        # do some initial GET request for getting the csrftoken
        session.get(self._url, headers=self._headers)

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
                         files=files, headers=self._headers)

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
