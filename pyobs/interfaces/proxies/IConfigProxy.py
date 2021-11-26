from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IConfigProxy(InterfaceProxy):
    def get_config_caps(self) -> 'Future[typing.Dict[str, typing.Tuple[bool, bool, bool]]]':
        ...

    def get_config_value(self, name: str) -> 'Future[typing.Any]':
        ...

    def get_config_value_options(self, name: str) -> 'Future[typing.List[str]]':
        ...

    def set_config_value(self, name: str, value: typing.Any) -> 'Future[None]':
        ...

