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
    __module__ = 'pyobs.mixins'

    def __init__(self, weather: Optional[Union[str, IWeather]] = None, **kwargs: Any):
        self.__weather = weather
        self.__is_weather_good: Optional[bool] = None
        this = self
        if isinstance(self, Module):
            self.add_background_task(this.__weather_check, True)
        else:
            raise ValueError('This is not a module.')

    async def open(self) -> None:
        """Open mixin."""
        # subscribe to events
        this = self
        if isinstance(self, Module) and self.comm is not None:
            await self.comm.register_event(BadWeatherEvent, this.__on_bad_weather)
            await self.comm.register_event(GoodWeatherEvent, this._on_good_weather)

    def __on_bad_weather(self, event: Event, sender: str) -> bool:
        """Abort exposure if a bad weather event occurs.

        Args:
            event: The bad weather event.
            sender: Who sent it.
        """

        # check
        if not isinstance(event, BadWeatherEvent):
            raise ValueError('Wrong event type.')

        # weather is bad
        self.__is_weather_good = False

        # do we need to park?
        if isinstance(self, MotionStatusMixin) and isinstance(self, IMotion):
            if self.get_motion_status() != MotionStatus.PARKED:
                log.warning('Received bad weather event, shutting down.')
                self.park()
            return True
        else:
            log.error('This is not a MotionStatusMixin/IMotion.')
            return False

    def _on_good_weather(self, event: Event, sender: str) -> bool:
        """Change status of weather.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """

        # check
        if not isinstance(event, GoodWeatherEvent):
            raise ValueError('Wrong event type.')

        # weather is good
        self.__is_weather_good = True
        return True

    async def __weather_check(self) -> None:
        """Thread for continuously checking for good weather"""

        # module?
        this = self
        if isinstance(self, Module):
            module = self

            # wait a little
            await event_wait(self.closing, 10)

            # time of last park attempt
            last_park_attempt = None

            # run until closing
            while not module.closing.is_set():
                # got a weather module?
                if this.__weather is None:
                    # weather is always good
                    this.__is_weather_good = True

                else:
                    try:
                        # get proxy
                        weather: IWeather = module.proxy(this.__weather, IWeather)

                        # get good status
                        this.__is_weather_good = await weather.is_weather_good()

                    except:
                        # could either not connect or weather is not good
                        this.__is_weather_good = False

                # if not good, park now
                if isinstance(self, MotionStatusMixin) and isinstance(self, IMotion):
                    if this.__is_weather_good is False and \
                            self.get_motion_status() not in [MotionStatus.PARKED, MotionStatus.PARKING]:
                        try:
                            asyncio.create_task(self.park())
                            log.info('Weather seems to be bad, shutting down.')
                        except:
                            # only log, if last attempt is more than 60s ago
                            # this is useful, so that we don't get log messages every 10 seconds but only the first one
                            # in a series
                            if last_park_attempt is None or time.time() - last_park_attempt > 60:
                                log.error('Could not park on bad weather.')

                        # store attempt time
                        last_park_attempt = time.time()

                else:
                    raise ValueError('This is not a MotionStatusMixin/IMotion.')

                # sleep a little
                await event_wait(module.closing, 10)

        else:
            # not a module
            raise ValueError('This is not a module.')

    def is_weather_good(self) -> bool:
        return self.__is_weather_good is True


__all__ = ['WeatherAwareMixin']
