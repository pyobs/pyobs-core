import asyncio
import logging
from asyncio import Task
from typing import Any

from pyobs.images.processor import ImageProcessor
from pyobs.images import Image
from pyobs.interfaces import IFitsHeaderBefore

log = logging.getLogger(__name__)


class GetFitsHeaders(ImageProcessor):
    """
    Retrieve and merge FITS header entries from one or more external modules.

    This asynchronous processor requests FITS header key–value pairs from modules
    implementing the ``IFitsHeaderBefore`` interface and merges them into a copy of
    the input image’s header. Requests are issued concurrently to all configured
    senders; results are applied in the order the senders are listed. If multiple
    modules provide the same header key, later modules overwrite earlier ones. Pixel
    data are not modified.

    :param str | list[str] sender: Name or list of names of modules to query. Each
                                   module must implement the ``IFitsHeaderBefore``
                                   interface providing a ``get_fits_header_before(namespace)`` method.
    :param str | None namespace: Optional namespace identifier forwarded to
                                 ``get_fits_header_before`` to allow modules to return
                                 context-specific headers (e.g., per pipeline stage).
                                 Default: ``None``.
    :param kwargs: Additional keyword arguments forwarded to
                   :class:`pyobs.images.processor.ImageProcessor`.

    Behavior
    --------
    - For each sender, obtains a proxy and calls
      ``proxy.get_fits_header_before(namespace)`` concurrently.
    - Creates a copy of the input image and merges returned headers into
      ``out.header`` in sender-list order.
    - Values that are lists (but not strings) are converted to tuples before insertion,
      ensuring FITS-header-friendly types. All other values are inserted as-is.
    - Returns the modified copy; pixel data and catalog are unchanged.

    Input/Output
    ------------
    - Input: :class:`pyobs.images.Image`.
    - Output: :class:`pyobs.images.Image` (copied) with additional or updated FITS
      header entries provided by the external modules.

    Configuration (YAML)
    --------------------
    Single sender:

    .. code-block:: yaml

       class: pyobs.images.processors.modules.GetFitsHeaders
       sender: "HeaderProviderA"

    Multiple senders with a namespace:

    .. code-block:: yaml

       class: pyobs.images.processors.modules.GetFitsHeaders
       sender: ["HeaderProviderA", "HeaderProviderB"]
       namespace: "preproc"

    Notes
    -----
    - Merging order follows the list of ``sender`` names; later senders overwrite
      earlier values for duplicate keys.
    - The modules must implement the ``IFitsHeaderBefore`` interface and be reachable
      via the ``proxy`` mechanism in this environment.
    - Converting lists to tuples helps store composite values in FITS headers; if a
      module encodes a value/comment pair as a list, it will become a tuple on insert.
    """

    __module__ = "pyobs.images.processors.modules"

    def __init__(self, sender: str | list[str], namespace: str | None = None, **kwargs: Any):
        """Init a fits header processor.

        Args:
            sender: Sender(s) to fetch FITS headers from.
            namespace: FITS namespace.
        """
        ImageProcessor.__init__(self, **kwargs)

        self._senders = [sender] if isinstance(sender, str) else sender
        self._namespace = namespace

    async def __call__(self, image: Image) -> Image:
        """Retrieve FITS headers from another module (or more).

        Args:
            image: Image to add headers to.

        Returns:
            Image with headers added.
        """

        # loop all modules
        requests: list[Task[Any]] = []
        for sender in self._senders:
            # get proxy
            proxy = await self.proxy(sender, IFitsHeaderBefore)

            # request headers
            requests.append(asyncio.create_task(proxy.get_fits_header_before(self._namespace)))

        # copy image
        out = image.copy()

        # await all requests
        for request in requests:
            hdr = await request
            for key, value in hdr.items():
                if isinstance(value, list) and not isinstance(value, str):
                    # convert list to tuple
                    out.header[key] = tuple(value)
                else:
                    out.header[key] = value
        return out


__all__ = ["GetFitsHeaders"]
