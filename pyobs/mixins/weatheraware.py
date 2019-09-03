import typing
import logging
import threading

from pyobs.events import BadWeatherEvent, GoodWeatherEvent
from pyobs.interfaces import IWeather, IMotion
from pyobs.comm import Comm


log = logging.getLogger(__name__)


class WeatherAwareMixin:
    _add_thread_func = None     # type: callable
    park = None                 # type: callable
    proxy = None                # type: callable
    comm = None                 # type: Comm
    _motion_status = None       # type: IMotion.Status
    closing = None              # type: threading.Event

    """Mixin for IMotion devices that should park(), when weather gets bad."""
    def __init__(self, weather: typing.Union[str, IWeather] = None, *args, **kwargs):
        self.__weather = weather
        self.__is_weather_good = None
        self._add_thread_func(self.__weather_check, True)

    def open(self):
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
        if self._motion_status != IMotion.Status.PARKED:
            log.warning('Received bad weather event, shutting down.')
            self.park()

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

        # wait a little
        self.closing.wait(10)

        # run until closing
        while not self.closing.is_set():
            # got a weather module?
            if self.__weather is None:
                # weather is always good
                self.__is_weather_good = True

            else:
                # get proxy
                weather: IWeather = self.proxy(self.__weather, IWeather)

                # get good status
                try:
                    self.__is_weather_good = weather.is_weather_good()
                except:
                    self.__is_weather_good = False

            # if not good, park now
            if self.__is_weather_good is False and self._motion_status != IMotion.Status.PARKED:
                log.warning('Weather seems to be bad, shutting down.')
                self.park()

            # sleep a little
            self.closing.wait(10)

    def is_weather_good(self):
        return self.__is_weather_good


__all__ = ['WeatherAwareMixin']
