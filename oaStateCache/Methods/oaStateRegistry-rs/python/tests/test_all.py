import pytest
import oaStateRegistry_rs


def test_sum_as_string():
    assert oaStateRegistry_rs.sum_as_string(1, 1) == "2"
