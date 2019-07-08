import pytest
import astroplan


def pytest_addoption(parser):
    parser.addoption("--use-ssh", action="store_true", help="do SSH tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "ssh: mark test as using SSH")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--use-ssh"):
        # do not skip slow tests
        return
    nossh = pytest.mark.skip(reason="SSH testing disabled (use --use-ssh to activate.")
    for item in items:
        if "ssh" in item.keywords:
            item.add_marker(nossh)


@pytest.fixture(scope="session", autouse=True)
def download_IERS():
    # before starting any test, download the new IERS data
    astroplan.download_IERS_A()
