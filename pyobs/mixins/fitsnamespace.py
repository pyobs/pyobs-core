import logging

from pyobs import PyObsModule

log = logging.getLogger(__name__)


class FitsNamespaceMixin:
    """Mixin for IFitsHeaderProvider modules that filters FITS headers by namespace."""
    def __init__(self, fits_namespaces: dict = None, *args, **kwargs):
        self.__namespaces = fits_namespaces

    def _filter_fits_namespace(self, hdr: dict, namespaces: list, sender: str, *args, **kwargs):
        """Filter FITS header keywords by given namespaces. If no namespaces are given, let all through. Always
        let keywords with this module's name as namespace pass.

        Args:
            hdr: Input header to filter
            namespaces: Requested namespaces
            sender: Name of module that requested headers

        Returns:
            Filtered FITS header
        """

        # no namespaces?
        if self.__namespaces is None or namespaces is None:
            return hdr

        # get list of FITS headers that we let pass
        keywords = []

        # is the sender name in my namespaces?
        if sender in self.__namespaces:
            # add namespace
            self.__add_namespace(sender, keywords, hdr)

        # loop all given namespaces
        for name in namespaces:
            # does namespace exist in my config?
            if name in self.__namespaces:
                # add namespace
                self.__add_namespace(name, keywords, hdr)

        # make unique
        keywords = list(set(keywords))

        # return filtered header
        return {k: v for k, v in hdr.items() if k in keywords}

    def __add_namespace(self, name: str, keywords: list, hdr: dict):
        """Add FITS header keywords from namespace to list of valid keywords

        Args:
            name: Name of namespace
            keywords: List of valid keywords, which will be added to
            hdr: Full unfiltered header
        """

        # no namespaces given at all? then add all...
        if self.__namespaces is None:
            keywords.extend(hdr.keys())
            return

        # given namespace doesn't exist? then add none
        if name not in self.__namespaces:
            return

        # what to add?
        if self.__namespaces[name] is None:
            # take all keywords, if namespace is empty or none are given
            keywords.extend(hdr.keys())
        elif isinstance(self.__namespaces[name], list):
            # take only keywords from list
            keywords.extend(self.__namespaces[name])
        else:
            log.error('Unknown namespace format: %s', self.__namespaces[name])


__all__ = ['FitsNamespaceMixin']
