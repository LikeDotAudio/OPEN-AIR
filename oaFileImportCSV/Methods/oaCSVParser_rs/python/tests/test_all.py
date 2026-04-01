import pytest
import oaCSVParser_rs


def test_sum_as_string():
    assert oaCSVParser_rs.sum_as_string(1, 1) == "2"
