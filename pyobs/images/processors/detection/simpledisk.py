import logging
from typing import Any

import numpy as np
import scipy.ndimage as ndi

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image


log = logging.getLogger(__name__)


class SimpleDisk(ImageProcessor):
    """
    Detect a roughly circular bright disk by thresholding and distance transform.

    This asynchronous processor segments the image by a fixed intensity threshold,
    selects the largest connected component, fills internal holes, and computes the
    Euclidean distance transform to find the pixel farthest from the component
    boundary. That pixel is taken as the disk center, and its distance to the
    boundary as the disk radius (both in pixels). The results are written into the
    FITS header under configurable keyword names. Pixel data are not modified.

    :param float | int threshold: Intensity threshold used to decide whether a pixel
                                  belongs to the disk (strictly ``data > threshold``).
                                  Units must match the image pixel values. Default: ``10.0``.
    :param str keyword_x: FITS header keyword to store the x-coordinate (column) of the
                          detected disk center (zero-based pixel index). Default: ``"DISKPOS1"``.
    :param str keyword_y: FITS header keyword to store the y-coordinate (row) of the
                          detected disk center (zero-based pixel index). Default: ``"DISKPOS2"``.
    :param str keyword_radius: FITS header keyword to store the disk radius in pixels.
                               Default: ``"DISKRAD"``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - Chooses the image plane: uses the first channel (``image.data[0, :, :]``) if the
      image is color, otherwise uses the full 2D array.
    - Creates a binary mask with ``mask = data > threshold``.
    - Labels connected components in the mask and keeps the largest one; if none are
      found, returns the original image unchanged.
    - Fills holes within the selected component and computes the Euclidean distance
      transform of the filled mask.
    - Finds the pixel ``(y, x)`` with maximum distance; sets ``radius = dist[y, x]``.
    - Returns a copy of the input image with the FITS header fields:
      - ``keyword_y`` = y (row index, zero-based)
      - ``keyword_x`` = x (column index, zero-based)
      - ``keyword_radius`` = radius (float, pixels)

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`
    - Output: :class:`pyobs.images.Image` (copied) with new FITS header entries for
      center coordinates and radius; pixel data are unchanged.

    Configuration (YAML)
    --------------------
    Basic detection with a custom threshold:

    .. code-block:: yaml

       class: pyobs.images.processors.disk.SimpleDisk
       threshold: 25.0

    Customize FITS header keywords:

    .. code-block:: yaml

       class: pyobs.images.processors.disk.SimpleDisk
       threshold: 15.0
       keyword_x: CX
       keyword_y: CY
       keyword_radius: CRAD

    Notes
    -----
    - Coordinates are reported as zero-based NumPy indices: ``(y, x) = (row, column)``.
      If you need FITS 1-based convention, add 1 when interpreting the values.
    - The algorithm assumes the disk is the largest bright connected region above the
      threshold. Choose ``threshold`` to robustly isolate the disk from background and
      other structures; pre-filtering or masking may help in noisy images.
    - The estimated radius is the in-mask inscribed-circle radius; for non-circular
      or partially occulted disks it represents the maximum interior distance to the
      boundary, not a best-fit circle.
    - Connectivity and hole filling use SciPy ndimage defaults; results may vary with
      image topology.
    """

    __module__ = "pyobs.images.processors.disk"

    def __init__(
        self,
        threshold: int | float = 10.0,
        keyword_x: str = "DISKPOS1",
        keyword_y: str = "DISKPOS2",
        keyword_radius: str = "DISKRAD",
        **kwargs: Any,
    ):
        """Init a new simple disk processor.

        Args:
            threshold: Threshold to determine if a pixel is on the disk.
        """
        ImageProcessor.__init__(self, **kwargs)

        # store
        self._threshold = threshold
        self._keyword_x = keyword_x
        self._keyword_y = keyword_y
        self._keyword_radius = keyword_radius

    async def __call__(self, image: Image) -> Image:
        """Detect a disk on image.

        Args:
            image: Image to use.

        Returns:
            Image with new FITS headers.
        """

        data = image.data[0, :, :] if image.is_color else image.data

        # mask according to threshold
        mask = data > self._threshold

        # Keep largest connected component
        lab, nlab = ndi.label(mask)
        if nlab == 0:
            return image
        counts = np.bincount(lab.ravel())
        counts[0] = 0  # background
        k = counts.argmax()
        comp = lab == k

        # Fill holes, then distance transform
        comp = ndi.binary_fill_holes(comp)
        dist = ndi.distance_transform_edt(comp)

        # get max
        y, x = np.unravel_index(np.argmax(dist), dist.shape)
        r = float(dist[y, x])

        # set it
        out = image.copy()
        out.header[self._keyword_y] = y
        out.header[self._keyword_x] = x
        out.header[self._keyword_radius] = r
        return out


__all__ = ["SimpleDisk"]
