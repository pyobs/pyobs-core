import pytest

from datetime import datetime
from pyobs.modules.pointing._baseguiding import _GuidingStatisticsUptime


def test_end_to_end():
    client = "camera"
    statistic = _GuidingStatisticsUptime()

    statistic.init_stats(client)

    statistic.add_data(True)

    header = statistic.add_to_header(client, {})

    assert header["GUIDING UPTIME"][0] == 100.0


def test_calc_uptime_percentage():
    states = [
        (True, datetime.fromtimestamp(100)),
        (False, datetime.fromtimestamp(110)),
        (None, datetime.fromtimestamp(120)),
    ]
    assert _GuidingStatisticsUptime()._calc_uptime_percentage(states) == 50
