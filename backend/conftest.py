import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--heavy",
        action="store_true",
        default=False,
        help="Run heavy tests that require MediaPipe/OpenCV and longer runtimes",
    )


def pytest_configure(config):
    # Default to LIGHT_MODE for tests unless --heavy is specified or env is already set
    if not config.getoption("--heavy") and "LIGHT_MODE" not in os.environ:
        os.environ["LIGHT_MODE"] = "1"
    # Ensure marker is registered even without pytest.ini
    config.addinivalue_line(
        "markers",
        "heavy: marks tests that require MediaPipe/OpenCV or long runtimes",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--heavy"):
        return
    skip_heavy = pytest.mark.skip(reason="Skipped in LIGHT_MODE; use --heavy to run")
    for item in items:
        if "heavy" in item.keywords:
            item.add_marker(skip_heavy)

