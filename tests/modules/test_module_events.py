"""Regression test for https://github.com/pyobs/pyobs-core/issues/845.

Module._on_module_opened is best-effort bookkeeping: if the sending module's
proxy can't be resolved (e.g. it already disconnected, or presence for it
hasn't arrived yet), the handler must swallow the failure and skip the
module rather than let the exception escape. The real XMPP backend hits
this by raising IndexError from get_interfaces() after its presence-wait
times out; Comm._get_client() turns that into a returned None, which
Comm._resolve_proxy() turns into a plain ValueError (not a PyobsError
subclass) -- so the handler must catch ValueError alongside PyobsError.
"""

from __future__ import annotations

import pytest

from pyobs.comm.dummy import DummyComm
from pyobs.events import ModuleOpenedEvent
from pyobs.interfaces import Interface
from pyobs.modules import Module

pytest_plugins = ("pytest_asyncio",)


class _PresenceTimeoutComm(DummyComm):
    """Mimics XmppComm.get_interfaces() raising IndexError once its presence wait times out."""

    async def get_interfaces(self, client: str) -> list[type[Interface]]:
        raise IndexError(f"No presence for {client}.")


@pytest.mark.asyncio
async def test_on_module_opened_skips_unresolvable_sender() -> None:
    module = Module(comm=_PresenceTimeoutComm())

    result = await module._on_module_opened(ModuleOpenedEvent(), "flatfield")

    assert result is True
