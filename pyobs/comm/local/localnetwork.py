from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .localcomm import LocalComm


class LocalNetwork:
    _instance: LocalNetwork | None = None

    def __new__(cls) -> LocalNetwork:
        if cls._instance is None:
            print("Creating the object")
            cls._instance = super().__new__(cls)

            cls._clients: dict[str, LocalComm] = {}

        return cls._instance

    def connect_client(self, comm: LocalComm) -> None:
        self._clients[comm.name] = comm

    def get_client(self, name: str) -> LocalComm:
        return self._clients[name]

    def get_clients(self) -> list[LocalComm]:
        return list(self._clients.values())

    def get_client_names(self) -> list[str]:
        return list(self._clients.keys())
