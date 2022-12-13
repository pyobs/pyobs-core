import asyncio
import logging
import time
from typing import Optional, Union, Any

from pyobs.interfaces import IWeather
from pyobs.modules import Module
from pyobs.events import BadWeatherEvent, GoodWeatherEvent, Event
from pyobs.interfaces import IMotion
from pyobs.mixins import MotionStatusMixin
from pyobs.utils.enums import MotionStatus
from pyobs.utils.parallel import event_wait

log = logging.getLogger(__name__)


class WeatherAwareMixin:
    """Mixin for IMotion devices that should park(), when weather gets bad."""

    __module__ = "pyobs.mixins"

    def __init__(self, weather: Optional[Union[str, IWeather]] = None, **kwargs: Any):
        self.__weather = weather
        self.__is_weather_good: Optional[bool] = None
        self.__last_park_attempt: Optional[float] = None
        self.__setting_bad_weather = False
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
        if self.__weather is not None and isinstance(self, Module) and self.comm is not None:
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
        # already setting?
        if self.__setting_bad_weather:
            return
        self.__setting_bad_weather = True

        # did weather change?
        if self.__is_weather_good is True:
            # weather is bad now
            self.__is_weather_good = False

            # do we need to park?
            if isinstance(self, MotionStatusMixin) and isinstance(self, IMotion):
                motion_status = await self.get_motion_status()
                if motion_status == MotionStatus.ERROR:
                    log.error("Telescope is in error mode, cannot park.")
                elif motion_status != MotionStatus.PARKED:
                    log.warning("Weather is bad, shutting down.")
                    await self.park()
            else:
                log.error("This is not a MotionStatusMixin/IMotion.")

        # finished
        self.__setting_bad_weather = False

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
                        # get proxy
                        weather: IWeather = await module.proxy(this.__weather, IWeather)

                        # get good status
                        this.__is_weather_good = await weather.is_weather_good()

                    except:
                        # could either not connect or weather is not good
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
        return self.__is_weather_good is True


__all__ = ["WeatherAwareMixin"]
