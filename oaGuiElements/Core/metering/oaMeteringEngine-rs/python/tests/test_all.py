import pytest
import oaMeteringEngine_rs


def test_sum_as_string():
    assert oaMeteringEngine_rs.sum_as_string(1, 1) == "2"
