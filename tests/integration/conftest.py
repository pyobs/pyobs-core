from __future__ import annotations

import pytest

from pyobs.comm.local.localnetwork import LocalNetwork


@pytest.fixture(autouse=True)
def reset_network():
    LocalNetwork._instance = None
    yield
    LocalNetwork._instance = None


def connect(module, name: str):
    """Connect a module to LocalComm and return the comm."""
    from pyobs.comm.local.localcomm import LocalComm

    comm = LocalComm(name)
    comm.module = module
    module._comm = comm
    return comm
