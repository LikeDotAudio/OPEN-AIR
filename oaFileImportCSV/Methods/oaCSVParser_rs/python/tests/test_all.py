import pytest

def test_sum_as_string():
    try:
        from oacsvparser_rs.oacsvparser_rs import sum_as_string
    except ImportError:
        try:
            from oacsvparser_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oacsvparser_rs")
            return
            
    assert sum_as_string(1, 1) == "2"
