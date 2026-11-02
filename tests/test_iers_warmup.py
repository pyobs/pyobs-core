"""_warm_iers_cache must trigger astropy's stale-table refresh itself (open() alone does not),
and fall back to the bundled table if that refresh fails."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import pyobs.application as app_module


def test_warm_up_does_time_lookups(monkeypatch: pytest.MonkeyPatch) -> None:
    table = MagicMock()
    monkeypatch.setattr("astropy.utils.iers.IERS_Auto.open", lambda: table)
    monkeypatch.setattr("astropy.time.core.update_leap_seconds", MagicMock())
    disable = MagicMock()
    monkeypatch.setattr(app_module, "_disable_iers_auto_download", disable)

    app_module._warm_iers_cache()

    table.ut1_utc.assert_called_once()
    table.pm_xy.assert_called_once()
    disable.assert_not_called()


def test_warm_up_failure_disables_auto_download(monkeypatch: pytest.MonkeyPatch) -> None:
    table = MagicMock()
    table.pm_xy.side_effect = ValueError("predictive values too old")
    monkeypatch.setattr("astropy.utils.iers.IERS_Auto.open", lambda: table)
    monkeypatch.setattr("astropy.time.core.update_leap_seconds", MagicMock())
    disable = MagicMock()
    monkeypatch.setattr(app_module, "_disable_iers_auto_download", disable)

    with pytest.raises(ValueError):
        app_module._warm_iers_cache()

    disable.assert_called_once()
