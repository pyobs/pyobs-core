"""Tests for the IVideo interface's VideoCapabilities dataclass."""

from __future__ import annotations

from pyobs.comm.xmpp.serializer import _dataclass_to_xml, _xml_to_dataclass
from pyobs.interfaces import VideoCapabilities


def test_video_capabilities_defaults() -> None:
    caps = VideoCapabilities()
    assert caps.mjpeg is None
    assert caps.raw is None


def test_video_capabilities_roundtrip() -> None:
    caps = VideoCapabilities(mjpeg="/webcam/video.mjpg", raw="/webcam/video.raw")
    xml = _dataclass_to_xml(caps, tag="capabilities")
    restored = _xml_to_dataclass(xml, VideoCapabilities)
    assert restored == caps


def test_video_capabilities_roundtrip_none_field() -> None:
    caps = VideoCapabilities(mjpeg="/webcam/video.mjpg", raw=None)
    xml = _dataclass_to_xml(caps, tag="capabilities")
    restored = _xml_to_dataclass(xml, VideoCapabilities)
    assert restored.mjpeg == "/webcam/video.mjpg"
    assert restored.raw is None
