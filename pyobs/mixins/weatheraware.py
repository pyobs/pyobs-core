import logging
import time
from typing import Optional, Union

from pyobs.modules import Module
from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather, IMotion
from pyobs.mixins import MotionStatusMixin
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)


class WeatherAwareMixin:
    """Mixin for IMotion devices that should park(), when weather gets bad."""
    def __init__(self, weather: Union[str, IWeather] = None, *args, **kwargs):
        self.__weather = weather
        self.__is_weather_good: Optional[bool] = None
        if isinstance(self, Module):
            self.add_thread_func(self.__weather_check, True)
        else:
            raise ValueError('This is not a module.')

    def open(self):
        """Open mixin."""
        # subscribe to events
        if self.comm:
            self.comm.register_event(BadWeatherEvent, self.__on_bad_weather)
            self.comm.register_event(GoodWeatherEvent, self._on_good_weather)

    def __on_bad_weather(self, event: BadWeatherEvent, sender: str, *args, **kwargs):
        """Abort exposure if a bad weather event occurs.

        Args:
            event: The bad weather event.
            sender: Who sent it.
        """

        # weather is bad
        self.__is_weather_good = False

        # do we need to park?
        if isinstance(self, MotionStatusMixin) and isinstance(self, IMotion):
            if self.get_motion_status() != MotionStatus.PARKED:
                log.warning('Received bad weather event, shutting down.')
                self.park()
        else:
            raise ValueError('This is not a MotionStatusMixin/IMotion.')

    def _on_good_weather(self, event: GoodWeatherEvent, sender: str, *args, **kwargs):
        """Change status of weather.

        Args:
            event: The good weather event.
            sender: Who sent it.
        """

        # weather is good
        self.__is_weather_good = True

    def __weather_check(self):
        """Thread for continuously checking for good weather"""

        # module?
        if isinstance(self, Module):
            # wait a little
            self.closing.wait(10)

            # time of last park attempt
            last_park_attempt = None

            # run until closing
            while not self.closing.is_set():
                # got a weather module?
                if self.__weather is None:
                    # weather is always good
                    self.__is_weather_good = True

                else:
                    try:
                        # get proxy
                        weather: IWeather = self.proxy(self.__weather, IWeather)

                        # get good status
                        self.__is_weather_good = weather.is_weather_good().wait()

                    except:
                        # could either not connect or weather is not good
                        self.__is_weather_good = False

                # if not good, park now
                if isinstance(self, MotionStatusMixin) and isinstance(self, IMotion):
                    if self.__is_weather_good is False and \
                            self.get_motion_status() not in [MotionStatus.PARKED, MotionStatus.PARKING]:
                        try:
                            self.park()
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
                self.closing.wait(10)

        else:
            # not a module
            raise ValueError('This is not a module.')

    def is_weather_good(self):
        return self.__is_weather_good


__all__ = ['WeatherAwareMixin']
