from datetime import datetime
from typing import List, Dict, Tuple, Any

from pyobs.modules.pointing.guidingstatistics.guidingstatistics import GuidingStatistics


class GuidingStatisticsUptime(GuidingStatistics):
    @staticmethod
    def _calc_uptime(states: List[Tuple[bool, datetime]]) -> int:
        uptimes: List[int] = []
        for i, entry in enumerate(states):
            state, timestamp = entry
            # is not closed?
            if not state or i + 1 == len(states):
                continue

            uptime = (states[i + 1][1] - timestamp).seconds
            uptimes.append(uptime)

        return sum(uptimes)

    @staticmethod
    def _calc_total_time(states: List[Tuple[bool, datetime]]) -> int:
        initial_time = states[0][1]
        end_time = states[-1][1]
        return (end_time - initial_time).seconds

    @staticmethod
    def _calc_uptime_percentage(states: List[Tuple[bool, datetime]]) -> float:
        uptime = GuidingStatisticsUptime._calc_uptime(states)
        total_time = GuidingStatisticsUptime._calc_total_time(states)

        """
        If no time has passed, return 100 if the loop is closed, 0 else.
        We have to take the second last value in the state array, since the last value is the stop value.
        """
        if total_time == 0:
            return int(states[-2][0]) * 100.0

        return uptime / total_time * 100.0

    def _build_header(self, data: List[Tuple[bool, datetime]]) -> Dict[str, Tuple[Any, str]]:
        now = datetime.now()
        data.append((None, now))

        uptime_percentage = self._calc_uptime_percentage(data)
        return {"GUIDING UPTIME": (uptime_percentage, "Time the guiding loop was closed [%]")}

    def _get_session_data(self, input_data: bool) -> Tuple[bool, datetime]:
        now = datetime.now()
        return input_data, now


__all__ = ['GuidingStatisticsUptime']