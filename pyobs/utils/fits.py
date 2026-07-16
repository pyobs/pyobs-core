"""
TODO: write doc
"""

__title__ = "FITS utilities"

import logging
import re
from collections.abc import Callable
from typing import Any, cast

from astropy.io import fits
from numpy.typing import NDArray

from pyobs.utils.time import Time

log = logging.getLogger(__name__)


def parse_section_bounds(header: fits.Header, keyword: str = "TRIMSEC") -> tuple[int, int, int, int] | None:
    """Parse a FITS section keyword (e.g. TRIMSEC) into 0-based, half-open slice bounds.

    Args:
        header: Header to look up the keyword in.
        keyword: Header keyword for section.

    Returns:
        (x0, x1, y0, y1) such that data[y0:y1, x0:x1] gives the section, or None if
        the keyword is not present in the header.

    Raises:
        ValueError: If the keyword is present but its value is malformed.
    """

    # keyword not given?
    if keyword not in header:
        return None

    # get value of section
    sec = header[keyword]

    # split values
    try:
        s = sec[1:-1].split(",")
        x = s[0].split(":")
        y = s[1].split(":")
        x0 = int(x[0]) - 1
        x1 = int(x[1])
        y0 = int(y[0]) - 1
        y1 = int(y[1])
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid {keyword} value: {sec!r}") from e

    return x0, x1, y0, y1


def fitssec(hdu: Any, keyword: str = "TRIMSEC") -> NDArray[Any]:
    """Trim an image to TRIMSEC or BIASSEC.

    Args:
        hdu: HDU to take data from.
        keyword: Header keyword for section.

    Returns:
        Numpy array with image data.
    """

    # parse section bounds
    bounds = parse_section_bounds(hdu.header, keyword)
    if bounds is None:
        # return whole data
        return cast(NDArray[Any], hdu.data)

    # return data
    x0, x1, y0, y1 = bounds
    return cast(NDArray[Any], hdu.data[y0:y1, x0:x1])


class FilenameFormatter:
    def __init__(self, fmt: str | list[str], keys: dict[str, int | float | str] | None = None):
        """Initializes a new filename formatter.

        Args:
            fmt: Filename format or list of formats. If list is given, first valid one is used.
            keys: Additional keys to pass to the formatter.
        """
        self.format = fmt
        self.keys: dict[str, int | float | str] = {} if keys is None else keys

        # define functions
        self.funcs: dict[str, Callable[..., str]] = {
            "lower": self._format_lower,
            "time": self._format_time,
            "date": self._format_date,
            "filter": self._format_filter,
            "string": self._format_string,
            "type": self._format_type,
        }

    def _value(self, hdr: fits.Header, key: str) -> int | float | str:
        """Returns value for given key.

        Args:
            hdr: fits.Header to take value from.
            key: Key to return value for.

        Returns:
            Value for given key.
        """

        # first check keys
        if key in self.keys:
            return self.keys[key]

        # then check header
        return cast(int | float | str, hdr[key])

    def __call__(self, hdr: fits.Header) -> str:
        """Formats a filename given a format template and a FITS header.

        Args:
            hdr: FITS header to take values from.

        Returns:
            Formatted filename.

        Raises:
            KeyError: If either keyword could not be found in header or method could not be found.
        """

        # make fmt a list
        if self.format is None:
            return ""
        if isinstance(self.format, str):
            self.format = [self.format]

        # loop formats
        for f in self.format:
            try:
                # find all placeholders in format
                placeholders = re.findall(r"\{[\w\d_-]+(?:\|[\w\d_-]+\:?(?:[\w\d_-]+)*)?\}", f)
                if len(placeholders) == 0:
                    return f

                # create output
                output = f

                # loop all placeholders
                for ph in placeholders:
                    # call method and replace
                    output = output.replace(ph, str(self._format_placeholder(ph, hdr)))

                # finished
                return output

            except KeyError:
                # this format didn't work
                pass

        # still here?
        raise KeyError("No valid format found.")

    def _format_placeholder(self, placeholder: str, hdr: fits.Header) -> str:
        """Format a given placeholder.

        Args:
            placeholder: Placeholder to format.
            hdr: FITS header to take values from.

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
        if "|" in key:
            key, method = key.split("|")

        # parameters for method?
        if method is not None and ":" in method:
            method, *params = method.split(":")

        # if no method is given, just replace
        if method is None:
            return str(self._value(hdr, key))

        else:
            # get function (may raise KeyError)
            func = self.funcs[method]

            # call method and replace
            return func(hdr, key, *params)

    def _format_lower(self, hdr: fits.Header, key: str) -> str:
        """Sets a given string to lowercase.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.

        Returns:
            Formatted string.
        """
        return str(self._value(hdr, key)).lower()

    def _format_time(self, hdr: fits.Header, key: str, delimiter: str = "-") -> str:
        """Formats time using the given delimiter.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.
            delimiter: Delimiter for time formatting.

        Returns:
            Formatted string.
        """
        fmt = "%H" + delimiter + "%M" + delimiter + "%S"
        date_obs = Time(self._value(hdr, key))
        return str(date_obs.datetime.strftime(fmt))

    def _format_date(self, hdr: fits.Header, key: str, delimiter: str = "-") -> str:
        """Formats date using the given delimiter.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.
            delimiter: Delimiter for date formatting.

        Returns:
            Formatted string.
        """
        fmt = "%Y" + delimiter + "%m" + delimiter + "%d"
        date_obs = Time(self._value(hdr, key))
        return str(date_obs.datetime.strftime(fmt))

    def _format_filter(self, hdr: fits.Header, key: str, image_type: str = "IMAGETYP", prefix: str = "-") -> str:
        """Formats a filter, prefixed by a given separator, only if the image type requires it.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.
            image_type: FITS header key for IMAGETYP.
            prefix: Prefix to add to filter.

        Returns:
            Formatted string.
        """
        it = hdr[image_type].lower()
        if it in ["light", "object", "flat", "skyflat"]:
            return prefix + str(self._value(hdr, key))
        else:
            return ""

    def _format_string(self, hdr: fits.Header, key: str, fmt: str) -> str:
        """Formats a string using Python string substitution.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.
            fmt: A Python string format like %d, %05d, or %4.1f.

        Returns:
            Formatted string.
        """
        fmt = "%" + fmt
        return str(fmt % self._value(hdr, key))

    def _format_type(self, hdr: fits.Header, key: str) -> str:
        """Formats an image type to a one-letter code.

        Args:
            hdr: FITS header to take values from.
            key: The name of the FITS header key to use.

        Returns:
            Formatted string.
        """
        if self._value(hdr, key) == "bias":
            return "b"
        elif self._value(hdr, key) == "skyflat":
            return "f"
        elif self._value(hdr, key) == "dark":
            return "d"
        else:
            return "e"


def format_filename(hdr: fits.Header, fmt: str | list[str], keys: dict[str, Any] | None = None) -> str:
    """Formats a filename given a format template and a FITS header.

    Args:
        hdr: FITS header to take values from.
        fmt: Filename format or list of formats. If multiple formats are given, the first valid one is used.
        keys: Additional keys to pass to the format string.

    Returns:
        Filename

    Raises:
        KeyError: If either keyword could not be found in header or method could not be found.
    """

    ff = FilenameFormatter(fmt, keys)
    return ff(hdr)


__all__ = ["format_filename", "FilenameFormatter", "fitssec", "parse_section_bounds"]
