from typing import Dict, Any


class WeatherState(object):
    def __init__(self) -> None:
        self._state: Dict[str, Any] = {"good": False}

    @property
    def is_good(self) -> bool:
        return bool(self._state["good"])

    @is_good.setter
    def is_good(self, is_good: bool) -> None:
        self._state["good"] = is_good

    @property
    def status(self) -> Dict[str, Any]:
        return self._state

    @status.setter
    def status(self, state: Dict[str, Any]) -> None:
        if "good" not in state:
            raise ValueError("Good parameter not found in response from weather station.")

        self._state = state
