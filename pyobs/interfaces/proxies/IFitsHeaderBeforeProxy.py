from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IFitsHeaderBeforeProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def get_fits_header_before(self, namespaces: typing.Optional[typing.List[str]] = None) -> 'Future[typing.Dict[str, typing.Tuple[typing.Any, str]]]':
        ...

