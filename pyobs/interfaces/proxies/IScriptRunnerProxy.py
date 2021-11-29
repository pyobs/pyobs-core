from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IScriptRunnerProxy(InterfaceProxy):
    __module__ = 'pyobs.interfaces.proxies'

    def run_script(self, script: str) -> 'Future[None]':
        ...

