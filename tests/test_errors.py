from __future__ import annotations

import pytest

from parc_ferme.errors import (
    ParcFermeError,
    ConfigError,
    GitHubError,
    PRNotFoundError,
    ReviewError,
    ToolNotFoundError,
)

ALL_SUBCLASSES = [
    ToolNotFoundError,
    PRNotFoundError,
    GitHubError,
    ConfigError,
    ReviewError,
]


def test_base_inherits_from_exception():
    assert issubclass(ParcFermeError, Exception)


@pytest.mark.parametrize("exc_class", ALL_SUBCLASSES)
def test_all_exceptions_inherit_from_base(exc_class):
    assert issubclass(exc_class, ParcFermeError)


@pytest.mark.parametrize("exc_class", ALL_SUBCLASSES)
def test_exception_message(exc_class):
    err = exc_class("something went wrong")
    assert str(err) == "something went wrong"


@pytest.mark.parametrize("exc_class", ALL_SUBCLASSES)
def test_catch_by_base_class(exc_class):
    with pytest.raises(ParcFermeError):
        raise exc_class("test")
