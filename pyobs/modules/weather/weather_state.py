from __future__ import annotations

from typing import Any


class WeatherState(object):
    def __init__(self) -> None:
        self._state: dict[str, Any] = {"good": False}

    @property
    def is_good(self) -> bool:
        return bool(self._state["good"])

    @is_good.setter
    def is_good(self, is_good: bool) -> None:
        self._state["good"] = is_good

    @property
    def status(self) -> dict[str, Any]:
        return self._state

    @status.setter
    def status(self, state: dict[str, Any]) -> None:
        if "good" not in state:
            raise ValueError("Good parameter not found in response from weather station.")

        if state["good"] is None:
            state["good"] = False

        self._state = state
