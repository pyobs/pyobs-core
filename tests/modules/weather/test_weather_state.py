import pytest

from pyobs.modules.weather.weather_state import WeatherStatus


def test_status_set_non_good():
    weather_status = WeatherStatus()
    with pytest.raises(ValueError):
        weather_status.status = {}


def test_status_set_none_good():
    weather_status = WeatherStatus()
    weather_status.status = {"good": None}

    assert weather_status.status["good"] is False


def test_status_set():
    weather_status = WeatherStatus()
    weather_status.status = {"good": True}

    assert weather_status.status["good"] is True
