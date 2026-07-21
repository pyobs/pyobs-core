from __future__ import annotations

import asyncio
import logging
from typing import Any

from pyobs.events import BadWeatherEvent, Event, GoodWeatherEvent
from pyobs.interfaces import IMotion, IWeather
from pyobs.mixins import MotionStatusMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class WeatherAwareMixin:
    """Mixin for IMotion devices that should park(), when weather gets bad."""

    __module__ = "pyobs.mixins"

    def __init__(self, weather: str | IWeather | None = None, **kwargs: Any):
        self.__weather = weather
        self.__is_weather_good: bool | None = None
        self.__last_park_attempt: float | None = None
        self.__weatheraware_is_error_state = False
        self.__weatheraware_lock = asyncio.Lock()
        self.__weather_check_failures = 0
        this = self
        if isinstance(self, Module):
            if weather is not None:
                self.add_background_task(this.__weather_check, True)
        else:
            raise ValueError("This is not a module.")

    async def open(self) -> None:
        """Open mixin."""
        # subscribe to events
        this = self
        if self.__weather is not None and isinstance(self, Module) and self._comm is not None:
            await self.comm.register_event(BadWeatherEvent, this.__on_bad_weather)
            await self.comm.register_event(GoodWeatherEvent, this._on_good_weather)

    async def __on_bad_weather(self, event: Event, sender: str) -> bool:
        """Abort exposure if a bad weather event occurs.

        Args:
            event: The bad weather event.
            sender: Who sent it.
        """

        # check
        if not isinstance(event, BadWeatherEvent):
            raise ValueError("Wrong event type.")

        # park
        asyncio.create_task(self.__set_bad_weather())
        return True

    async def __set_bad_weather(self) -> None:
        # locked?
        if self.__weatheraware_lock.locked():
            return

        # get lock
        async with self.__weatheraware_lock:
            # get motion status and error state
            msi = self
            if isinstance(msi, MotionStatusMixin) and isinstance(msi, IMotion):
                motion_status = msi.motion_status() if hasattr(msi, "motion_status") else MotionStatus.UNKNOWN
                is_error_state = motion_status == MotionStatus.ERROR
            else:
                log.error("This is not a MotionStatusMixin/IMotion.")
                return

            # do we need to park?
            if motion_status not in [MotionStatus.PARKED, MotionStatus.PARKING]:
                # error state?
                if is_error_state and not self.__weatheraware_is_error_state:
                    log.error("Telescope is in error mode, cannot park.")
                else:
                    # parking?
                    if motion_status != MotionStatus.PARKED:
                        log.warning("Weather is bad, shutting down.")
                        await msi.park()

            # save error state
            self.__weatheraware_is_error_state = is_error_state

    async def _on_good_weather(self, event: Event, sender: str) -> bool:
        """Change status of weather.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """

        # check
        if not isinstance(event, GoodWeatherEvent):
            raise ValueError("Wrong event type.")

        # weather is good
        self.__is_weather_good = True
        return True

    async def __weather_check(self) -> None:
        """Thread for continuously checking for good weather"""

        # module?
        this = self
        if isinstance(self, Module):
            module = self

            # run until closing
            while True:
                # got a weather module?
                if this.__weather is None:
                    # weather is always good
                    this.__is_weather_good = True

                else:
                    try:
                        # get good status
                        async with module.proxy(this.__weather, IWeather) as proxy:
                            weather_state = await proxy.wait_for_state(IWeather, timeout=5.0)
                            this.__is_weather_good = weather_state.good if weather_state is not None else False
                        this.__weather_check_failures = 0

                    except Exception:
                        # could not reach the weather module. This can be a real outage, but
                        # right after startup it's usually just that presence/roster hasn't
                        # settled yet, so don't jump to "bad weather" (and park) on the very
                        # first hiccup -- only once it persists across a few checks.
                        this.__weather_check_failures += 1
                        if this.__weather_check_failures >= 3:
                            this.__is_weather_good = False

                # if not good, park now
                if this.__is_weather_good is False:
                    asyncio.create_task(this.__set_bad_weather())

                # sleep a little
                await asyncio.sleep(10)

        else:
            # not a module
            raise ValueError("This is not a module.")

    def is_weather_good(self) -> bool:
        if self.__weather is None:
            return True
        else:
            return self.__is_weather_good is True


__all__ = ["WeatherAwareMixin"]
