import io
import logging
import os

import PIL
import aplpy
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.io.fits import Header
from pytel.utils.time import Time
from pytel.modules.environment import Environment


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
    
    # get date-obs of image
    date_obs = Time(hdr['DATE-OBS'])
    image_type = hdr['IMAGETYP']

    # {night} in pattern?
    if '{night}' in fmt:
        # no environment?
        if environment is None:
            log.warning('No environment given for evaluating night.')
            fmt = fmt.replace('{night}', '')
        else:
            # get night, which serves as path
            night_obs = environment.night_obs(date_obs)
            fmt = fmt.replace('{night}', night_obs.strftime("%Y%m%d"))

    # {date} in pattern?
    if '{date}' in fmt:
        fmt = fmt.replace('{date}', date_obs.datetime.strftime('%Y-%m-%d'))

    # {time} in pattern?
    if '{time}' in fmt:
        fmt = fmt.replace('{time}', date_obs.datetime.strftime('%H-%M-%S'))

    # {type} in pattern?
    if '{type}' in fmt:
        fmt = fmt.replace('{type}', '_' + image_type)

    # {filter} in pattern?
    if '{filter}' in fmt:
        replace = '_' + hdr['FILTER'] if 'FILTER' in hdr and image_type.lower() not in ['dark', 'bias'] else ''
        fmt = fmt.replace('{filter}', replace)

    # {path} in pattern?
    if '{path}' in fmt:
        fmt = fmt.replace('{path}', os.path.dirname(filename))

    # {filename} in pattern?
    if '{filename}' in fmt:
        fmt = fmt.replace('{filename}', os.path.basename(filename))

    # {telescope} in pattern?
    if '{telescope}' in fmt:
        fmt = fmt.replace('{telescope}', hdr['TELESCOP'].lower())

    # replace double slashes
    return fmt.replace('//', '/')


__all__ = ['create_preview', 'format_filename']
