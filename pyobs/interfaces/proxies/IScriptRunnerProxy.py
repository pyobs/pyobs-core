import typing

from pyobs.utils.threads import Future
from .interfaceproxy import InterfaceProxy


class IScriptRunnerProxy(InterfaceProxy):
    def run_script(self, script: str) -> Future[None]:
        ...

