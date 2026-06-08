import pytest

from pyobs.comm.local import LocalComm, LocalNetwork


@pytest.fixture(autouse=True)
def reset_network() -> None:
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


def test_singleton() -> None:
    net1 = LocalNetwork()
    net2 = LocalNetwork()
    assert net1 is net2


def test_connect_client() -> None:
    net = LocalNetwork()
    client = LocalComm("test")
    assert "test" in net._clients
    assert net._clients["test"] is client


def test_get_client() -> None:
    net = LocalNetwork()
    client = LocalComm("test")
    assert net.get_client("test") is client


def test_get_clients() -> None:
    net = LocalNetwork()
    client = LocalComm("test")
    assert client in net.get_clients()


def test_get_client_names() -> None:
    net = LocalNetwork()
    LocalComm("cam")
    LocalComm("tel")
    names = net.get_client_names()
    assert "cam" in names
    assert "tel" in names


def test_multiple_clients() -> None:
    net = LocalNetwork()
    c1 = LocalComm("camera")  # noqa: F841
    c2 = LocalComm("telescope")  # noqa: F841
    assert len(net.get_clients()) == 2
