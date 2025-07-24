from __future__ import annotations
from typing import Dict, List, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .localcomm import LocalComm


class LocalNetwork:
    _instance: Optional["LocalNetwork"] = None

    def __new__(cls) -> "LocalNetwork":
        if cls._instance is None:
            print("Creating the object")
            cls._instance = super(LocalNetwork, cls).__new__(cls)

            cls._clients: Dict[str, LocalComm] = {}

        return cls._instance

    def connect_client(self, comm: LocalComm) -> None:
        self._clients[comm.name] = comm

    def get_client(self, name: str) -> LocalComm:
        return self._clients[name]

    def get_clients(self) -> List[LocalComm]:
        return list(self._clients.values())

    def get_client_names(self) -> List[str]:
        return list(self._clients.keys())
