from __future__ import annotations

from typing import Dict, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pyobs.comm


class LocalNetwork:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print('Creating the object')
            cls._instance = super(LocalNetwork, cls).__new__(cls)

            cls._clients: Dict[str, pyobs.comm.local.LocalComm] = {}

        return cls._instance

    def connect(self, name: str, comm: pyobs.comm.local.LocalComm):
        self._clients[name] = comm

    def get_client(self, name: str) -> pyobs.comm.local.LocalComm:
        return self._clients[name]

    def get_clients(self) -> List[pyobs.comm.local.LocalComm]:
        return list(self._clients.values())

    def get_client_names(self) -> List[str]:
        return list(self._clients.keys())
