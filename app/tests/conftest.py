"""Shared test setup. Owner: A.

Tests never use the network (SPEC rule 14.10). The guard in `tests/network_guard.py` is switched on before any
test file is imported, so it also covers module-level code and module or session fixtures. A test that tries to
reach the network fails, even if its code catches the error. Use the saved files in `app/evidence/` or
`app/tests/fixtures/` instead.
"""

import pytest

from tests import network_guard


def pytest_configure(config):
    network_guard.install()


def pytest_unconfigure(config):
    network_guard.uninstall()


@pytest.fixture(autouse=True)
def _fail_if_the_test_tried_the_network():
    before = len(network_guard.ATTEMPTS)
    yield
    tried = network_guard.ATTEMPTS[before:]
    if tried:
        pytest.fail(f"This test tried to reach the network ({sorted(set(map(str, tried)))}); SPEC rule 14.10.")


def pytest_sessionfinish(session, exitstatus):
    # Attempts outside a test (at import, in module or session fixtures) also fail the run.
    if network_guard.ATTEMPTS and session.exitstatus == 0:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line(f"Network attempts outside tests: {network_guard.ATTEMPTS} (SPEC rule 14.10)", red=True)
        session.exitstatus = 1
