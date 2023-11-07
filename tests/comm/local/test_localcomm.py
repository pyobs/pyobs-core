import pytest
from typing import Any

from pyobs.comm.local import LocalNetwork, LocalComm
from pyobs.events import Event, GoodWeatherEvent
from pyobs.interfaces import ICamera, IExposureTime, IImageType, IModule, IConfig
from pyobs.mixins import ImageFitsHeaderMixin
from pyobs.modules import Module
from pyobs.modules.camera import BaseCamera
from pyobs.utils.enums import ImageType


def test_init():
    comm = LocalComm("test")

    assert comm._name == "test"
    assert comm._network.get_client("test") == comm


def test_name():
    comm = LocalComm("test")

    assert comm.name == "test"


def test_clients(mocker):
    comm = LocalComm("test")

    clients = ["test", "telescope", "camera"]
    mocker.patch.object(comm._network, "get_client_names", return_value=clients)

    assert comm.clients == clients


class TestModule(Module, IImageType):

    async def set_image_type(self, image_type: ImageType, **kwargs: Any) -> None:
        pass

    async def get_image_type(self, **kwargs: Any) -> ImageType:
        return ImageType.BIAS


@pytest.mark.asyncio
async def test_get_interfaces(mocker):
    comm = LocalComm("test")

    another_comm = LocalComm("camera")
    another_comm.module = TestModule()

    mocker.patch.object(comm._network, "get_client", return_value=another_comm)

    interfaces = await comm.get_interfaces("camera")

    assert set(interfaces) == {IConfig, IImageType, IModule}
    comm._network.get_client.assert_called_once_with("camera")


@pytest.mark.asyncio
async def test_supports_interface(mocker):
    comm = LocalComm("test")

    mocker.patch.object(comm, "get_interfaces", return_value=[IConfig, IImageType, IModule])

    assert comm._supports_interface("camera", IConfig)


@pytest.mark.asyncio
async def test_execute(mocker):
    comm = LocalComm("test")

    another_comm = LocalComm("camera")
    another_comm.module = TestModule()

    mocker.patch.object(comm._network, "get_client", return_value=another_comm)

    assert await comm.execute("camera", "get_image_type", {"return": ImageType}) == ImageType.BIAS
    comm._network.get_client.assert_called_once_with("camera")


@pytest.mark.asyncio
async def test_send_event(mocker):
    comm = LocalComm("test")

    another_comm = LocalComm("camera")
    another_comm.module = TestModule()

    mocker.patch.object(comm._network, "get_clients", return_value=[another_comm])
    mocker.patch.object(another_comm, "_send_event_to_module")

    await comm.send_event(Event())
    another_comm._send_event_to_module.assert_called_once()

