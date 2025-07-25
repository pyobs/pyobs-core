from __future__ import annotations
import copy
import io
from typing import TypeVar, Optional, Type, Any, cast
import numpy as np
import numpy.typing as npt
from astropy.io import fits
from astropy.io.fits import table_to_hdu, ImageHDU
from astropy.table import Table
from astropy.nddata import CCDData, StdDevUncertainty
from numpy.typing import NDArray

from pyobs.utils.fits import FilenameFormatter
import pyobs.utils.exceptions as exc

MetaClass = TypeVar("MetaClass")


class Image:
    """Image class."""

    __module__ = "pyobs.images"

    def __init__(
        self,
        data: npt.NDArray[np.floating[Any]] | None = None,
        header: fits.Header | None = None,
        mask: npt.NDArray[np.floating[Any]] | None = None,
        uncertainty: npt.NDArray[np.floating[Any]] | None = None,
        catalog: Table | None = None,
        raw: npt.NDArray[np.floating[Any]] | None = None,
        meta: dict[Any, Any] | None = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Init a new image.

        Args:
            data: Numpy array containing data for image.
            header: Header for the new image.
            mask: Mask for the image.
            uncertainty: Uncertainty image.
            catalog: Catalog table.
            raw: If image is calibrated, this should be the raw image.
            meta: Dictionary with meta information (note: not preserved in I/O operations!).
        """

        # store
        self._data: npt.NDArray[np.floating[Any]] | None = data
        self._header = fits.Header() if header is None else header.copy()
        self._mask: npt.NDArray[np.floating[Any]] | None = None if mask is None else mask.copy()
        self._uncertainty: npt.NDArray[np.floating[Any]] | None = (
            None if uncertainty is None else uncertainty.copy()
        )
        self._catalog = None if catalog is None else catalog.copy()
        self._raw: npt.NDArray[np.floating[Any]] | None = None if raw is None else raw.copy()
        self._meta = {} if meta is None else copy.deepcopy(meta)

        # add basic header stuff
        if data is not None and self._header is not None:
            self.header["NAXIS1"] = data.shape[1]
            self.header["NAXIS2"] = data.shape[0]

    @classmethod
    def from_bytes(cls, data: bytes) -> Image:
        """Create Image from a bytes array containing a FITS file.

        Args:
            data: Bytes array to create image from.

        Returns:
            The new image.
        """

        # create hdu
        with io.BytesIO(data) as bio:
            # read whole file
            d = fits.open(bio, memmap=False, lazy_load_hdus=False)

            # load image
            return cls._from_hdu_list(d)

    @classmethod
    def from_file(cls, filename: str) -> Image:
        """Create image from FITS file.

        Args:
            filename: Name of file to load image from.

        Returns:
            New image.
        """

        with fits.open(filename, memmap=False, lazy_load_hdus=False) as data:
            return cls._from_hdu_list(data)

    @classmethod
    def from_ccddata(cls, data: CCDData) -> Image:
        """Create image from astropy.CCDData.

        Args:
            data: CCDData to create image from.

        Returns:
            New image.
        """

        # create image and assign data
        image = Image(
            data=data.data.astype(np.float32),
            header=data.header,
            mask=data.mask,
            uncertainty=None if data.uncertainty is None else data.uncertainty.array.astype(np.float32),
        )
        return image

    @classmethod
    def _from_hdu_list(cls, data: fits.HDUList) -> "Image":
        """Load Image from HDU list.

        Args:
            data: HDU list.

        Returns:
            Image.
        """

        # create image
        image = cls()

        # find HDU with image data
        for hdu in data:
            if (
                isinstance(hdu, fits.PrimaryHDU)
                and hdu.header["NAXIS"] > 0
                or isinstance(hdu, fits.ImageHDU)
                and hdu.name == "SCI"
                or isinstance(hdu, fits.CompImageHDU)
            ):
                # found image HDU
                image_hdu = hdu
                break
        else:
            raise ValueError("Could not find HDU with main image.")

        # get data
        image._data = image_hdu.data
        image._header = image_hdu.header

        # mask
        if "MASK" in data:
            image._mask = data["MASK"].data

        # uncertainties
        if "UNCERT" in data:
            image._uncertainty = data["UNCERT"].data

        # catalog
        if "CAT" in data:
            image._catalog = Table(data["CAT"].data)

        # raw
        if "RAW" in data:
            image._raw = data["RAW"].data

        # finished
        return image

    @property
    def unit(self) -> str:
        """Returns units of pixels in image."""
        if "BUNIT" in self.header:
            return str(self.header["BUNIT"]).lower()
        else:
            return "adu"

    def __deepcopy__(self) -> Image:
        """Returns a shallow copy of this image."""
        return self.copy()

    def copy(self) -> Image:
        """Returns a copy of this image."""
        return Image(
            data=self._data,
            header=self._header,
            mask=self._mask,
            uncertainty=self._uncertainty,
            catalog=self._catalog,
            raw=self._raw,
            meta=self._meta,
        )

    def __truediv__(self, other: Image) -> Image:
        """Divides this image by other."""
        img = self.copy()
        if img._data is not None and other._data is not None:
            img._data = img._data / other._data
            return img
        else:
            raise ValueError("One image in division is None.")

    def writeto(self, f: Any, *args: Any, **kwargs: Any) -> None:
        """Write image as FITS to given file object.

        Args:
            f: File object to write to.
        """

        # create HDU list
        hdu_list = fits.HDUList([])

        # create image HDU
        hdu = fits.PrimaryHDU(self.data, header=self.header)
        hdu_list.append(hdu)

        # catalog?
        if self._catalog is not None:
            hdu = table_to_hdu(self._catalog)
            hdu.name = "CAT"
            hdu_list.append(hdu)

        # mask?
        if self._mask is not None:
            hdu = ImageHDU(self._mask.astype(np.uint8))
            hdu.name = "MASK"
            hdu_list.append(hdu)

        # errors?
        if self._uncertainty is not None:
            hdu = ImageHDU(self._uncertainty.data)
            hdu.name = "UNCERT"
            hdu_list.append(hdu)

        # raw?
        if self._raw is not None:
            hdu = ImageHDU(self._raw.data)
            hdu.name = "RAW"
            hdu_list.append(hdu)

        # write it
        hdu_list.writeto(f, *args, **kwargs)

    def to_bytes(self) -> bytes:
        """Write to a bytes array and return it."""
        with io.BytesIO() as bio:
            self.writeto(bio)
            return bio.getvalue()

    def write_catalog(self, f: Any, *args: Any, **kwargs: Any) -> None:
        """Write catalog to file object."""
        if self._catalog is None:
            return

        hdu = table_to_hdu(self._catalog)
        hdu.writeto(f, *args, **kwargs)

    def to_ccddata(self) -> CCDData:
        """Convert Image to CCDData"""
        return CCDData(
            data=self._data,
            meta=self._header,
            mask=self._mask,
            uncertainty=None if self._uncertainty is None else StdDevUncertainty(self._uncertainty),
            unit="adu",
        )

    def format_filename(self, formatter: FilenameFormatter) -> str:
        """Format filename with given formatter."""
        self._header["FNAME"] = formatter(self._header)
        return str(self._header["FNAME"])

    @property
    def pixel_scale(self) -> Optional[float]:
        """Returns pixel scale in arcsec/pixel."""
        if "CD1_1" in self._header:
            return abs(float(self._header["CD1_1"])) * 3600.0
        elif "CDELT1" in self._header:
            return abs(float(self._header["CDELT1"])) * 3600.0
        else:
            return None

    def to_jpeg(self, vmin: Optional[float] = None, vmax: Optional[float] = None) -> bytes:
        """Returns a JPEG image created from this image.

        Returns:
            The image.
        """

        # import PIL Image
        import PIL.Image

        # copy data
        data: NDArray[Any] = np.copy(self._data)  # type: ignore
        if data is None:
            raise ValueError("No data in image.")

        # no vmin/vmax?
        if vmin is None or vmax is None:
            flattened = sorted(data.flatten())
            vmin = flattened[int(0.05 * len(flattened))]
            vmax = flattened[int(0.95 * len(flattened))]
            if vmin is None or vmax is None:
                raise ValueError("Could not determine vmin/vmax.")

        # Clip data to brightness limits
        data[data > vmax] = vmax
        data[data < vmin] = vmin

        # Scale data to range [0, 1]
        data = (data - vmin) / (vmax - vmin)

        # Convert to 8-bit integer
        data = (255 * data).astype(np.uint8)

        # Invert y axis
        data = data[::-1, :]

        # create image from data array
        image = PIL.Image.fromarray(data, "L")
        with io.BytesIO() as bio:
            image.save(bio, format="jpeg")
            return bio.getvalue()

    def set_meta(self, meta: Any) -> None:
        """Sets meta information, storing it under it class.

        Note that it is possible to store, e.g., strings, but they would be stored as img.meta[str] and be overwritten
        with every new string, which is probably not what you want. Use the img.meta dict directly for this and
        set_meta/get_meta only for class-based data.

        Args:
            meta: Meta information to store.
        """

        # store it
        self._meta[meta.__class__] = meta

    def has_meta(self, meta_class: Type[MetaClass]) -> bool:
        """Whether meta exists."""
        return meta_class in self._meta

    def get_meta(self, meta_class: Type[MetaClass]) -> MetaClass:
        """Returns meta information, assuming that it is stored under the class of the object.

        Args:
            meta_class: Class to return meta information for.

        Returns:
            Meta information of the given class.
        """
        # return default?
        if meta_class not in self._meta:
            raise ValueError("Meta value not found.")

        # correct type?
        if not isinstance(self._meta[meta_class], meta_class):
            raise ValueError("Stored meta information is of wrong type.")

        # return it
        return cast(MetaClass, self._meta[meta_class])

    def get_meta_safe(self, meta_class: Type[MetaClass], default: Optional[MetaClass] = None) -> Optional[MetaClass]:
        """Calls get_meta in a safe way and returns default value in case of an exception."""

        try:
            return self.get_meta(meta_class)
        except:
            return default

    @property
    def safe_data(self) -> Optional[npt.NDArray[np.floating[Any]]]:
        return self._data

    @property
    def data(self) -> npt.NDArray[np.floating[Any]]:
        if self._data is None:
            raise exc.ImageError("No data found in image.")
        return self._data

    @data.setter
    def data(self, val: Optional[npt.NDArray[np.floating[Any]]]) -> None:
        self._data = val

    @property
    def safe_header(self) -> Optional[fits.Header]:
        return self._header

    @property
    def header(self) -> fits.Header:
        if self._header is None:
            raise exc.ImageError("No header found in image.")
        return self._header

    @header.setter
    def header(self, val: Optional[fits.Header]) -> None:
        self._header = val

    @property
    def safe_mask(self) -> npt.NDArray[np.floating[Any]] | None:
        return self._mask

    @property
    def mask(self) -> npt.NDArray[np.floating[Any]]:
        if self._mask is not None:
            return self._mask
        else:
            raise exc.ImageError("No mask found in image.")

    @mask.setter
    def mask(self, val: npt.NDArray[np.floating[Any]] | None) -> None:
        self._mask = val

    @property
    def safe_uncertainty(self) -> npt.NDArray[np.floating[Any]] | None:
        return self._uncertainty

    @property
    def uncertainty(self) -> npt.NDArray[np.floating[Any]]:
        if self._uncertainty is None:
            raise exc.ImageError("No uncertainties found in image.")
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, val: npt.NDArray[np.floating[Any]] | None) -> None:
        self._uncertainty = val

    @property
    def safe_catalog(self) -> Table | None:
        return self._catalog

    @property
    def catalog(self) -> Table:
        if self._catalog is None:
            raise exc.ImageError("No catalog found in image.")
        return self._catalog

    @catalog.setter
    def catalog(self, val: Table | None) -> None:
        self._catalog = val

    @property
    def safe_raw(self) -> npt.NDArray[np.floating[Any]] | None:
        return self._raw

    @property
    def raw(self) -> npt.NDArray[np.floating[Any]]:
        if self._raw is None:
            raise exc.ImageError("No raw data found in image.")
        return self._raw

    @raw.setter
    def raw(self, val: npt.NDArray[np.floating[Any]] | None) -> None:
        self._raw = val

    @property
    def meta(self) -> dict[Any, Any]:
        if self._meta is None:
            self._meta = {}
        return self._meta

    @meta.setter
    def meta(self, val: Optional[dict[Any, Any]]) -> None:
        self._meta = {} if val is None else val


__all__ = ["Image"]
