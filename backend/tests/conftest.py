from uuid import uuid4

import pytest

import utils.rate_limit as rate_limit_module


@pytest.fixture
def company_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """Disable the rate limiter for every test.

    Without this fixture, tests that hit the same endpoint several times
    could trip the limit and fail non-deterministically.
    The dedicated 429 test overrides this behavior locally.
    """
    rate_limit_module.limiter.enabled = False
    yield
    rate_limit_module.limiter.enabled = True
