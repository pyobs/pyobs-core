import io
import numpy as np
from astropy.io import fits
from astropy.io.fits import table_to_hdu


class Image:
    def __init__(self, *args, **kwargs):
        self.data = None
        self.header = None
        self.catalog = None

    @staticmethod
    def from_bytes(data) -> 'Image':
        # create hdu
        with io.BytesIO(data) as bio:
            # read whole file
            data = fits.open(bio, memmap=False, lazy_load_hdus=False)

            # store
            image = Image()
            image.data = data['SCI'].data
            image.header = data['SCI'].header

            # close file
            data.close()
            return image

    def copy(self):
        img = Image()
        img.data = self.data.copy()
        img.header = self.header
        return img

    def __truediv__(self, other):
        img = self.copy()
        img.data /= other
        return img

    def writeto(self, f, *args, **kwargs):
        # create HDU list
        hdu_list = fits.HDUList([])

        # create image HDU
        hdu = fits.PrimaryHDU(self.data, header=self.header)
        hdu_list.append(hdu)

        # catalog?
        if self.catalog is not None:
            hdu = table_to_hdu(self.catalog)
            hdu.name = 'CAT'
            hdu_list.append(hdu)

        # write it
        hdu_list.writeto(f, *args, **kwargs)

    def write_catalog(self, f, *args, **kwargs):
        if self.catalog is None:
            return

        # create HDU and write it
        table_to_hdu(self.catalog).writeto(f, *args, **kwargs)

    def _section(self, keyword: str = 'TRIMSEC') -> np.ndarray:
        """Trim an image to TRIMSEC or BIASSEC.

        Args:
            hdu: HDU to take data from.
            keyword: Header keyword for section.

        Returns:
            Numpy array with image data.
        """

        # keyword not given?
        if keyword not in self.header:
            # return whole data
            return self.data

        # get value of section
        sec = self.header[keyword]

        # split values
        s = sec[1:-1].split(',')
        x = s[0].split(':')
        y = s[1].split(':')
        x0 = int(x[0]) - 1
        x1 = int(x[1])
        y0 = int(y[0]) - 1
        y1 = int(y[1])

        # return data
        return self.data[y0:y1, x0:x1]

    def _subtract_overscan(self):
        # got a BIASSEC?
        if 'BIASSEC' not in self.header:
            return

        # get mean of BIASSEC
        biassec = np.mean(self._section('BIASSEC'))

        # subtract mean
        self.header['L1OVRSCN'] = (biassec, 'Subtracted mean BIASSEC counts')
        self.data -= biassec

    def trim(self):
        # TRIMSEC exists?
        if 'TRIMSEC' in self.header:
            # create new image
            img = self.copy()

            # trim data
            img.data = img._section('TRIMSEC')

            # adjust size in fits headers
            img.header['NAXIS2'], img.header['NAXIS1'] = img.data.shape

            # delete keywords
            for key in ['TRIMSEC', 'BIASSEC', 'DATASEC']:
                if key in img.header:
                    del img.header[key]

            # finished
            return img

        else:
            # don't do anything
            return self

    def calibrate(self, bias: 'BiasFrame' = None, dark: 'DarkFrame' = None, flat: 'FlatFrame' = None):
        # copy image
        img = self.copy()

        # to float32
        img.data = img.data.astype(np.float32)

        # subtract overscan
        img._subtract_overscan()

        # subtract bias
        if bias is not None:
            img.data -= bias.data
            img.header['L1BIAS'] = (bias.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                    'Name of BIAS frame')

        # subtract dark
        if dark is not None:
            img.data -= dark.data * img.header['EXPTIME']
            img.header['L1DARK'] = (dark.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                    'Name of DARK frame')

        # divide by flat
        if flat is not None:
            img.data /= flat.data
            img.header['L1FLAT'] = (flat.header['FNAME'].replace('.fits.fz', '').replace('.fits', ''),
                                   'Name of FLAT frame')

        # it's reduced now
        img.header['RLEVEL'] = 1

        # finished
        return img

    def format_filename(self, formatter):
        self.header['FNAME'] = formatter(self.header)


__all__ = ['Image']
