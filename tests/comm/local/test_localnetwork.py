from pyobs.comm.local import LocalNetwork, LocalComm


def test_singleton():
    net1 = LocalNetwork()
    net2 = LocalNetwork()

    assert net1 == net2


def test_connect_client():
    net = LocalNetwork()
    client = LocalComm("test")

    net.connect_client(client)

    assert client == net._clients["test"]


def test_get_client():
    net = LocalNetwork()
    client = LocalComm("test")

    net._clients = {"test": client}

    assert client == net.get_client("test")


def test_get_clients():
    net = LocalNetwork()
    client = LocalComm("test")

    net._clients = {"test": client}

    assert [client] == net.get_clients()


def test_get_client_names():
    net = LocalNetwork()
    client = LocalComm("test")

    net._clients = {"test": client}

    assert ["test"] == net.get_client_names()
