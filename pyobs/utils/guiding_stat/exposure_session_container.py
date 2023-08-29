from typing import Dict, List, Tuple


class ExposureSessionContainer:
    def __init__(self):
        self._sessions: Dict[str, List[Tuple[float, float]]] = dict()
