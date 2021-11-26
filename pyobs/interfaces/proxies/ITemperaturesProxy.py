from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class ITemperaturesProxy(InterfaceProxy):
    def get_temperatures(self) -> 'Future[typing.Dict[str, float]]':
        ...

