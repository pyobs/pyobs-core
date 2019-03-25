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


def format_filename(hdr: Header, fmt: str, environment: Environment = None, filename: str = None) -> str:
    """Formats a filename given a format template and a FITS header.

    Args:
        hdr (Header): FITS header to take values from.
        fmt (str): Filename format.
        environment (Environment): An environment used for calculating night of observation.
        filename (str): Original filename.

    Returns:
        (str) Filename
    """

    # find all placeholders in format
    placeholders = re.findall('\{\w+\}', fmt)

    # get date-obs of image
    date_obs = Time(hdr['DATE-OBS']) if 'DATE-OBS' in hdr else None

    # {night} in pattern?
    if '{night}' in placeholders:
        # date obs?
        if date_obs is None:
            raise KeyError('No DATE-OBS given for {night} pattern.')
        # get night, which serves as path
        night_obs = environment.night_obs(date_obs)
        fmt = fmt.replace('{night}', night_obs.strftime("%Y%m%d"))

    # {date} in pattern?
    if '{date}' in placeholders:
        # date obs?
        if date_obs is None:
            raise KeyError('No DATE-OBS given for {date} pattern.')
        # format it
        fmt = fmt.replace('{date}', date_obs.datetime.strftime('%Y-%m-%d'))

    # {time} in pattern?
    if '{time}' in placeholders:
        # date obs?
        if date_obs is None:
            raise KeyError('No DATE-OBS given for {time} pattern.')
        # format it
        fmt = fmt.replace('{time}', date_obs.datetime.strftime('%H-%M-%S'))

    # {type} in pattern?
    if '{type}' in placeholders:
        fmt = fmt.replace('{type}', '_' + hdr['IMAGETYP'])

    # {filter} in pattern?
    if '{filter}' in placeholders:
        # if image type is given, only add filter, if it makes sense
        if 'IMAGETYP' in hdr:
            replace = '_' + hdr['FILTER'] if hdr['IMAGETYP'].lower() not in ['dark', 'bias'] else ''
        else:
            replace = '_' + hdr['FILTER']
        # format it
        fmt = fmt.replace('{filter}', replace)

    # {path} in pattern?
    if '{path}' in placeholders:
        fmt = fmt.replace('{path}', os.path.dirname(filename))

    # {filename} in pattern?
    if '{filename}' in placeholders:
        fmt = fmt.replace('{filename}', os.path.basename(filename))

    # check FITS headers
    for p in placeholders:
        # remove curly brackets and get header keys (cannot do <key> in hdr, since that's case-insensitive)
        key = p[1:-1]
        header_keys = list(hdr.keys())
        # do we have a keyword of this name?
        if key in header_keys:
            print(key)
            # replace it
            fmt = fmt.replace(p, hdr[key])

    # any placeholders left?
    for p in placeholders:
        if p in fmt:
            raise KeyError('Placeholder %s could not be set.' % p)

    # replace double slashes
    return fmt.replace('//', '/')


__all__ = ['create_preview', 'format_filename']
