import pytest

from mako.stats.xp import compute_user_level


@pytest.mark.parametrize(
    "user_xp,user_level",
    [(0, 1), (2, 2), (3, 2), (4, 3), (8, 4), (10, 4), (12, 4), (16, 5), (32, 6)],
)
def test_compute_user_level(user_xp, user_level):
    assert compute_user_level(user_xp) == user_level
