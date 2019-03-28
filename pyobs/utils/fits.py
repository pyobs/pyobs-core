import io
import logging
import os
import re

import PIL
import aplpy
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.io.fits import Header
from pyobs.utils.time import Time
from pyobs.environment import Environment


log = logging.getLogger(__name__)


def create_preview(hdu: fits.PrimaryHDU, grid: bool = True, colorbar: bool = True,
                   mark_centre: bool = True, buffer=False) -> PIL.Image.Image:
    # create figure
    dpi = 100.
    fig = plt.figure(figsize=(780. / dpi, 780. / dpi), dpi=dpi)

    # create plot
    gc = aplpy.FITSFigure(hdu, figure=fig)
    gc.show_colorscale(cmap='gist_heat', stretch='arcsinh')

    # add colorbar and grid
    if colorbar:
        gc.add_colorbar()
    if grid:
        gc.add_grid()

    # mark position
    if 'CRVAL1' in hdu.header and 'CRVAL2' in hdu.header and mark_centre:
        gc.show_markers([hdu.header['CRVAL1']], [hdu.header['CRVAL2']], c='blue', marker='+')

    # create PIL image
    with io.BytesIO() as buf:
        # write to buffer
        fig.tight_layout()
        fig.savefig(buf, format='png', dpi=dpi*0.6)
        gc.close()

        # create PIL image
        im = PIL.Image.open(buf)

        # crop away white borders
        bg = PIL.Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = PIL.ImageChops.difference(im, bg)
        bbox = diff.getbbox()

        # return buffer or image?
        if buffer:
            with io.BytesIO() as buf:
                im.crop(bbox).save(buf, format='png')
                return buf.getvalue()
        else:
            return im.crop(bbox)


class FilenameFormatter:
    def __init__(self, hdr: Header, environment: Environment = None):
        """Initializes a new filename formatter.

        Args:
            hdr: FITS header to take values from.
            environment: Environment to use.
        """
        self.header = hdr
        self.environment = environment

        # define functions
        self.funcs = {
            'time': self._format_time,
            'date': self._format_date,
            'night': self._format_night,
            'filter': self._format_filter
        }

    def __call__(self, fmt: str):
        """Formats a filename given a format template and a FITS header.

        Args:
            fmt (str): Filename format.

        Returns:
            (str) Filename

        Raises:
            KeyError: If either keyword could not be found in header or method could not be found.
        """

        # find all placeholders in format
        placeholders = re.findall('\{[\w\d_-]+(?:\|[\w\d_-]+(?:\:[\w\d_-]+)*)?\}', fmt)
        if len(placeholders) == 0:
            return fmt

        # create output
        output = fmt

        # loop all placeholders
        for ph in placeholders:
            # call method and replace
            output = output.replace(ph, self._format_placeholder(ph))

        # finished
        return output

    def _format_placeholder(self, placeholder):
        # remove curly brackets
        key = placeholder[1:-1]
        method = None
        params = []

        # do we have a pipe in here?
        if '|' in key:
            key, method = key.split('|')

        # parameters for method?
        if method is not None and ':' in method:
            method, *params = method.split(':')

        # if no method is given, just replace
        if method is None:
            return self.header[key]

        else:
            # get function (may raise KeyError)
            func = self.funcs[method]

            # call method and replace
            return func(key, *params)

    def _format_time(self, key, delimiter=':'):
        fmt = '%H' + delimiter + '%M' + delimiter + '%S'
        date_obs = Time(self.header[key])
        return date_obs.datetime.strftime(fmt)


    def _format_date(self, key, delimiter='-'):
        fmt = '%Y' + delimiter + '%m' + delimiter + '%d'
        date_obs = Time(self.header[key])
        return date_obs.datetime.strftime(fmt)

    def _format_night(self, key, delimiter=''):
        date_obs = Time(self.header[key])
        night_obs = self.environment.night_obs(date_obs)
        return night_obs.strftime('%Y' + delimiter + '%m' + delimiter + '%d')

    def _format_filter(self, key, image_type='IMAGETYP', separator='_'):
        it = self.header[image_type].lower()
        if it in ['light', 'object']:
            return separator + self.header[key]
        else:
            return ''


def format_filename(hdr: Header, fmt: str, environment: Environment = None) -> str:
    """Formats a filename given a format template and a FITS header.

    Args:
        hdr (Header): FITS header to take values from.
        fmt (str): Filename format.
        environment (Environment): An environment used for calculating night of observation.

    Returns:
        (str) Filename

    Raises:
        KeyError: If either keyword could not be found in header or method could not be found.
    """

    ff = FilenameFormatter(hdr, environment)
    return ff(fmt)


__all__ = ['create_preview', 'format_filename', 'FilenameFormatter']
