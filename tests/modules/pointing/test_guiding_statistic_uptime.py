import pytest

from datetime import datetime
from pyobs.modules.pointing.guidingstatistics import GuidingStatisticsUptime


def test_end_to_end() -> None:
    client = "camera"
    statistic = GuidingStatisticsUptime()

    statistic.init_stats(client)

    statistic.add_data(True)

    header = statistic.add_to_header(client, {})

    assert header["GUIDING UPTIME"][0] == 100.0


def test_calc_uptime_percentage() -> None:
    states = [
        (True, datetime.fromtimestamp(100)),
        (False, datetime.fromtimestamp(110)),
        (None, datetime.fromtimestamp(120)),
    ]
    assert GuidingStatisticsUptime()._calc_uptime_percentage(states) == 50
