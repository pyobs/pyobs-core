from abc import abstractmethod, ABCMeta
from collections import defaultdict
from typing import Any, TypeVar, Generic

IN = TypeVar("IN")
OUT = TypeVar("OUT")


class GuidingStatistics(Generic[IN, OUT], object, metaclass=ABCMeta):
    """Calculates statistics for guiding."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Any]] = defaultdict(list)

    def init_stats(self, client: str, default: Any = None) -> None:
        """
        Inits a stat measurement session for a client.

        Args:
            client: name/id of the client
            default: first entry in session
        """

        self._sessions[client] = []

        if default is not None:
            self._sessions[client].append(self._get_session_data(default))

    @abstractmethod
    def _build_header(self, data: Any) -> dict[str, tuple[Any, str]]:
        raise NotImplementedError

    def add_to_header(self, client: str, header: dict[str, tuple[Any, str]]) -> dict[str, tuple[Any, str]]:
        """
        Add statistics to given header.

        Args:
            client: id/name of the client
            header: Header dict to add statistics to.
        """

        if client not in self._sessions:
            return header

        data = self._sessions.pop(client)
        session_header = self._build_header(data)

        return header | session_header

    @abstractmethod
    def _get_session_data(self, input_data: IN) -> OUT:
        raise NotImplementedError

    def add_data(self, input_data: IN) -> None:
        """
        Adds data to all client measurement sessions.
        Args:
            input_data: Image witch metadata
        """

        data = self._get_session_data(input_data)

        for k in self._sessions.keys():
            self._sessions[k].append(data)
