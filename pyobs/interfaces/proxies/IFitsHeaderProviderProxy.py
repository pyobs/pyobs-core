import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IFitsHeaderProviderProxy(InterfaceProxy):
    def get_fits_headers(self, namespaces: typing.Optional[typing.List[str]] = None) -> Future[typing.Dict[str, typing.Tuple[typing.Any, str]]]:
        ...

