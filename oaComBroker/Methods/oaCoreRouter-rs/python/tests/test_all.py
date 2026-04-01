import pytest
import oaCoreRouter_rs


def test_sum_as_string():
    assert oaCoreRouter_rs.sum_as_string(1, 1) == "2"
