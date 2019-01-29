import pytest


def pytest_addoption(parser):
    parser.addoption("--use-ssh", action="store_true", help="do SSH tests")
