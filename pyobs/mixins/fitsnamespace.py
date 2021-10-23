import logging
from typing import List, Dict, Optional, Any, Tuple


log = logging.getLogger(__name__)


class FitsNamespaceMixin:
    """Mixin for IFitsHeaderProvider modules that filters FITS headers by namespace."""
    __module__ = 'pyobs.mixins'

    def __init__(self, fits_namespaces: Optional[Dict[str, List[str]]] = None, **kwargs: Any):
        self.__namespaces = {} if fits_namespaces is None else fits_namespaces

    def _filter_fits_namespace(self, hdr: Dict[str, Tuple[Any, str]], sender: str,
                               namespaces: Optional[List[str]] = None) -> Dict[str, Tuple[Any, str]]:
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
        if not self.__namespaces:
            return hdr

        # get list of FITS headers that we let pass
        keywords: List[str] = []

        # is the sender name in my namespaces?
        if sender in self.__namespaces:
            # add namespace
            self.__add_namespace(sender, keywords, hdr)

        # loop all given namespaces
        if namespaces is not None:
            for name in namespaces:
                # does namespace exist in my config?
                if name in self.__namespaces:
                    # add namespace
                    self.__add_namespace(name, keywords, hdr)

        # make unique
        keywords = list(set(keywords))

        # return filtered header
        return {k: v for k, v in hdr.items() if k in keywords}

    def __add_namespace(self, name: str, keywords: List[str], hdr: Dict[str, Any]) -> None:
        """Add FITS header keywords from namespace to list of valid keywords

        Args:
            name: Name of namespace
            keywords: List of valid keywords, which will be added to
            hdr: Full unfiltered header
        """

        # what to add?
        if name not in self.__namespaces:
            # given namespace doesn't exist? then add none
            return
        elif self.__namespaces[name] is None:
            # take all keywords, if namespace is empty or none are given
            keywords.extend(hdr.keys())
        elif isinstance(self.__namespaces[name], list):
            # take only keywords from list
            keywords.extend(self.__namespaces[name])
        else:
            log.error('Unknown namespace format: %s', self.__namespaces[name])


__all__ = ['FitsNamespaceMixin']
