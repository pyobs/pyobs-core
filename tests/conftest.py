import os

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            if os.getenv("CI"):
                item.add_marker(pytest.mark.skip(reason="integration tests run separately on release"))
