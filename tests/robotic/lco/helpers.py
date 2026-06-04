"""Shared helpers for LCO tests."""

from __future__ import annotations
from unittest.mock import MagicMock

from pyobs.robotic.lco._portal import Portal
from pyobs.robotic.lco.taskarchive import LcoTaskArchive
from pyobs.robotic.lco.observationarchive import LcoObservationArchive


def make_portal() -> Portal:
    """Create Portal bypassing Object.__init__ and aiohttp session."""
    p = Portal.__new__(Portal)
    # PrivateAttrMixin attributes
    p._comm = None
    p._observer = None
    p._vfs = None
    p._timezone = None
    p._location = None
    # Portal attributes
    p.url = "http://localhost:8000"
    p.token = "token123"
    p.headers = {"Authorization": "Token token123"}
    p._site = "goe"
    p._enclosure = "roof"
    p._telescope = "0m5a"
    p.site = "goe"
    p.enclosure = "roof"
    p.telescope = "0m5a"
    p._session = MagicMock()
    return p


def make_task_archive(instrument_type: str = "0m5 iag50cm sbig6303e") -> LcoTaskArchive:
    """Create LcoTaskArchive without background tasks or Object.__init__."""
    archive = LcoTaskArchive.__new__(LcoTaskArchive)
    archive._comm = None
    archive._observer = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._portal = make_portal()
    archive._instrument_type = [instrument_type]
    archive._last_changed = None
    archive._tasks = []
    archive._projects = []
    archive._on_tasks_changed = None
    return archive


def make_observation_archive() -> LcoObservationArchive:
    """Create LcoObservationArchive without background tasks or Object.__init__."""
    archive = LcoObservationArchive.__new__(LcoObservationArchive)
    archive._comm = None
    archive._observer = None
    archive._vfs = None
    archive._timezone = None
    archive._location = None
    archive._portal = make_portal()
    return archive
