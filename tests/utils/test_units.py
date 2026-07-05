from __future__ import annotations

from abc import abstractmethod
from typing import Annotated, Any

import astropy.units as u
import pytest

from pyobs.interfaces.interface import Interface
from pyobs.utils.enums import Unit
from pyobs.utils.units import with_units


class IMove(Interface):
    @abstractmethod
    async def move(
        self, ra: Annotated[float, Unit.DEGREES], dec: Annotated[float, Unit.DEGREES], **kwargs: Any
    ) -> None: ...


class IFocus(Interface):
    @abstractmethod
    async def set_focus(self, focus: Annotated[float, Unit.MM], **kwargs: Any) -> None: ...


class IMultiUnit(Interface):
    @abstractmethod
    async def observe(
        self,
        ra: Annotated[float, Unit.DEGREES],
        exptime: Annotated[float, Unit.SECONDS],
        **kwargs: Any,
    ) -> None: ...


class IMixed(Interface):
    @abstractmethod
    async def configure(self, ra: Annotated[float, Unit.DEGREES], count: int, **kwargs: Any) -> None: ...


class Telescope(IMove):
    def __init__(self) -> None:
        self.received: tuple[Any, Any] | None = None

    @with_units
    async def move(self, ra: float, dec: float, **kwargs: Any) -> None:
        self.received = (ra, dec)


class Focuser(IFocus):
    def __init__(self) -> None:
        self.received: Any = None

    @with_units
    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        self.received = focus


class MultiUnitInstrument(IMultiUnit):
    def __init__(self) -> None:
        self.received: tuple[Any, Any] | None = None

    @with_units
    async def observe(self, ra: float, exptime: float, **kwargs: Any) -> None:
        self.received = (ra, exptime)


class MixedInstrument(IMixed):
    def __init__(self) -> None:
        self.received: tuple[Any, Any] | None = None

    @with_units
    async def configure(self, ra: float, count: int, **kwargs: Any) -> None:
        self.received = (ra, count)


@pytest.mark.asyncio
async def test_with_units_converts_degrees() -> None:
    t = Telescope()
    await t.move(180.0, 45.0)
    assert t.received == (180.0 * u.deg, 45.0 * u.deg)


@pytest.mark.asyncio
async def test_with_units_converts_mm() -> None:
    f = Focuser()
    await f.set_focus(12.5)
    assert f.received == 12.5 * u.mm


@pytest.mark.asyncio
async def test_with_units_converts_multiple_different_units() -> None:
    m = MultiUnitInstrument()
    await m.observe(90.0, 30.0)
    assert m.received == (90.0 * u.deg, 30.0 * u.s)


@pytest.mark.asyncio
async def test_with_units_leaves_non_annotated_params_unchanged() -> None:
    m = MixedInstrument()
    await m.configure(45.0, 3)
    ra, count = m.received
    assert ra == 45.0 * u.deg
    assert count == 3
    assert not isinstance(count, u.Quantity)


@pytest.mark.asyncio
async def test_with_units_kwargs_also_converted() -> None:
    t = Telescope()
    await t.move(ra=270.0, dec=-30.0)
    assert t.received == (270.0 * u.deg, -30.0 * u.deg)
