from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyobs.application import Application

from .pyobs import PyobsCLI


class PyobsWinCLI(PyobsCLI):
    """Class for initializing and running pyobs CLI."""

    # name of section in configuration file
    CONFIG_SECTION = "pyobs"

    # list of parameters that can be defined in the config file
    GLOBAL_CONFIG_KEYS = [
        "log_level",
        "influx_log",
        "debug_time",
    ]

    def application(self, **kwargs: Any) -> Application:
        from pyobs.application import GuiApplication

        return GuiApplication(**kwargs)


if __name__ == "__main__":
    cli = PyobsWinCLI()
    cli()
