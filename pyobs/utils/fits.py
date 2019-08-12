import io
import logging
import re
from typing import Union

import PIL
import aplpy
import matplotlib.pyplot as plt
from astroplan import Observer
from astropy.io import fits
from astropy.io.fits import Header
from pyobs.utils.time import Time


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
    def __init__(self, hdr: Header, observer: Observer = None, keys: dict = None):
        """Initializes a new filename formatter.

        Args:
            hdr: FITS header to take values from.
            observer: Observer to use.
            keys: Additional keys to pass to the formatter.
        """
        self.header = hdr
        self.observer = observer
        self.keys = {} if keys is None else keys

        # define functions
        self.funcs = {
            'lower': self._format_lower,
            'time': self._format_time,
            'date': self._format_date,
            'night': self._format_night,
            'filter': self._format_filter,
            'string': self._format_string,
            'type': self._format_type
        }

    def _value(self, key: str):
        """Returns value for given key.

        Args:
            key: Key to return value for.

        Returns:
            Value for given key.
        """

        # first check keys
        if key in self.keys:
            return self.keys[key]

        # then check header
        return self.header[key]

    def __call__(self, fmt: Union[str, list]) -> str:
        """Formats a filename given a format template and a FITS header.

        Args:
            fmt: Filename format or list of formats. If list is given, first valid one is used.

        Returns:
            Formatted filename.

        Raises:
            KeyError: If either keyword could not be found in header or method could not be found.
        """

        # make fmt a list
        if fmt is None:
            return
        if not isinstance(fmt, list):
            fmt = [fmt]

        # loop formats
        for f in fmt:
            try:
                # find all placeholders in format
                placeholders = re.findall('\{[\w\d_-]+(?:\|[\w\d_-]+\:?(?:[\w\d_-]+)*)?\}', f)
                if len(placeholders) == 0:
                    return f

                # create output
                output = f

                # loop all placeholders
                for ph in placeholders:
                    # call method and replace
                    output = output.replace(ph, self._format_placeholder(ph))

                # finished
                return output

            except KeyError:
                # this format didn't work
                pass

        # still here?
        raise KeyError('No valid format found.')

    def _format_placeholder(self, placeholder: str) -> str:
        """Format a given placeholder.

        Args:
            placeholder: Placeholder to format.

        Returns:
            Formatted placeholder.

        Raises:
            KeyError: If method or FITS header keyword don't exist.
        """

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
            return self._value(key)

        else:
            # get function (may raise KeyError)
            func = self.funcs[method]

            # call method and replace
            return func(key, *params)

    def _format_lower(self, key: str) -> str:
        """Sets a given string to lowercase.

       Args:
           key: The name of the FITS header key to use.

       Returns:
           Formatted string.
       """
        return self._value(key).lower()

    def _format_time(self, key: str, delimiter: str = '-') -> str:
        """Formats time using the given delimiter.

       Args:
           key: The name of the FITS header key to use.
           delimiter: Delimiter for time formatting.

       Returns:
           Formatted string.
       """
        fmt = '%H' + delimiter + '%M' + delimiter + '%S'
        date_obs = Time(self._value(key))
        return date_obs.datetime.strftime(fmt)

    def _format_date(self, key: str, delimiter: str = '-') -> str:
        """Formats date using the given delimiter.

        Args:
            key: The name of the FITS header key to use.
            delimiter: Delimiter for date formatting.

        Returns:
            Formatted string.
        """
        fmt = '%Y' + delimiter + '%m' + delimiter + '%d'
        date_obs = Time(self._value(key))
        return date_obs.datetime.strftime(fmt)

    def _format_night(self, key: str, delimiter: str = '') -> str:
        """Calculates night of DATE in given FITS keyword and format it using the given delimiter.

        Args:
            key: The name of the FITS header key to use.
            delimiter: Delimiter for date formatting.

        Returns:
            Formatted string.
        """
        date_obs = Time(self._value(key))
        night_obs = date_obs.night_obs(self.observer)
        return night_obs.strftime('%Y' + delimiter + '%m' + delimiter + '%d')

    def _format_filter(self, key: str, image_type: str = 'IMAGETYP', prefix: str = '_') -> str:
        """Formats a filter, prefixed by a given separator, only if the image type requires it.

        Args:
            key: The name of the FITS header key to use.
            image_type: FITS header key for IMAGETYP.
            prefix: Prefix to add to filter.

        Returns:
            Formatted string.
        """
        it = self.header[image_type].lower()
        if it in ['light', 'object', 'flat']:
            return prefix + self._value(key)
        else:
            return ''

    def _format_string(self, key: str, format: str) -> str:
        """Formats a string using Python string substitution.

        Args:
            key: The name of the FITS header key to use.
            format: A Python string format like %d, %05d, or %4.1f.

        Returns:
            Formatted string.
        """
        fmt = '%' + format
        return fmt % self._value(key)

    def _format_type(self, key: str) -> str:
        """Formats an image type to a one-letter code.

        Args:
            key: The name of the FITS header key to use.

        Returns:
            Formatted string.
        """
        if self._value('IMAGETYP') == 'bias':
            return 'b'
        elif self._value('IMAGETYP') == 'flat':
            return 'f'
        elif self._value('IMAGETYP') == 'd':
            return 'd'
        else:
            return 'e'


def format_filename(hdr: Header, fmt: Union[str, list], observer: Observer = None, keys: dict = None) -> str:
    """Formats a filename given a format template and a FITS header.

    Args:
        hdr: FITS header to take values from.
        fmt: Filename format or list of formats. If multiple formats are given, the first valid one is used.
        observer: An observer used astronomical calculations.
        keys: Additional keys to pass to the format string.

    Returns:
        Filename

    Raises:
        KeyError: If either keyword could not be found in header or method could not be found.
    """

    ff = FilenameFormatter(hdr, observer, keys)
    return ff(fmt)


__all__ = ['create_preview', 'format_filename', 'FilenameFormatter']
