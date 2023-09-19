from pyobs.utils.guiding_stat.exposure_session_container import ExposureSessionContainer


def test_init():
    esc = ExposureSessionContainer()
    assert esc._sessions == dict()


def test_init_session_new():
    esc = ExposureSessionContainer()
    esc.init_session("camera")
    assert esc._sessions["camera"] == []


def test_init_session_existing():
    esc = ExposureSessionContainer()
    esc._sessions = {"camera": [(0.0, 0.0), (1.1, 1.1)]}
    esc.init_session("camera")
    assert esc._sessions["camera"] == []


def test_pop_session():
    esc = ExposureSessionContainer()
    data = [(0.0, 0.0), (1.0, 1.0)]
    esc._sessions = {"camera": data}

    assert esc.pop_session("camera") == data
    assert "camera" not in esc._sessions


def test_add_data_to_all():
    esc = ExposureSessionContainer()
    data = [(0.0, 0.0)]
    esc._sessions = {"camera": data, "another": []}

    esc.add_data_to_all((2.0, 2.0))

    assert esc._sessions["camera"][0] == (0.0, 0.0)
    assert esc._sessions["camera"][1] == (2.0, 2.0)
    assert esc._sessions["another"][0] == (2.0, 2.0)
