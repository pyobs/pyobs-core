import inspect
from typing import Any
import pytest


def pytest_addoption(parser: Any) -> None:
    parser.addoption("--use-ssh", action="store_true", help="do SSH tests")


def pytest_configure(config: Any) -> None:
    config.addinivalue_line("markers", "ssh: mark test as using SSH")


def pytest_collection_modifyitems(config: Any, items: Any) -> None:
    # add asyncio decorator to all async methods
    for item in items:
        if inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

    # do SSH tests?
    if not config.getoption("--use-ssh"):
        nossh = pytest.mark.skip(reason="SSH testing disabled (use --use-ssh to activate.")
        for item in items:
            if "ssh" in item.keywords:
                item.add_marker(nossh)


@pytest.fixture(scope="session", autouse=True)
def download_IERS() -> None:
    # IERS workaround...
    from astropy.utils import iers
    from astropy.utils.data import clear_download_cache

    clear_download_cache()
    # iers.conf.auto_download = False
    # iers.conf.auto_max_age = None
    iers.IERS_Auto.open()
