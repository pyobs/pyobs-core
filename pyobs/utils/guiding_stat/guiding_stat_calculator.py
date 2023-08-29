from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer


class GuidingStatCalculator:
    def __init__(self, stat_meta_class: type[object]):
        self._stat_meta_class = stat_meta_class
        self._sessions = ExposureSessionContainer()

