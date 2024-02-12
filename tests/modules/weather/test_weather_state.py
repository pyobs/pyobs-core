import pytest

from pyobs.modules.weather.weather_state import WeatherState


def test_status_set_non_good():
    weather_state = WeatherState()
    with pytest.raises(ValueError):
        weather_state.status = {}


def test_status_set_none_good():
    weather_state = WeatherState()
    weather_state.status = {"good": None}

    assert weather_state.status["good"] is False


def test_status_set():
    weather_state = WeatherState()
    weather_state.status = {"good": True}

    assert weather_state.status["good"] is True
