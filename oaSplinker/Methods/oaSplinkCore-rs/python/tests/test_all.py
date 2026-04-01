import pytest
import oaSplinkCore_rs


def test_sum_as_string():
    assert oaSplinkCore_rs.sum_as_string(1, 1) == "2"
