from typing import Dict, List, Tuple


class ExposureSessionContainer:
    """Contains data recorded while an exposure"""
    def __init__(self):
        self._sessions: Dict[str, List[Tuple[float, float]]] = dict()

    def init_session(self, client: str) -> None:
        """
        Initializes a session for a client
        Args:
            client: name/id of the client
        """
        self._sessions[client] = []

    def pop_session(self, client: str) -> List[Tuple[float, float]]:
        """
        Ends the session for a client
        Args:
            client: name/id of the client

        Returns:
            Recorded session data
        """
        return self._sessions.pop(client)

    def add_data_to_all(self, data: Tuple[float, float]) -> None:
        """
        Adds data to all clients
        Args:
            data: Data to record
        """
        for client in self._sessions.keys():
            self._sessions[client].append(data)
