import pytest

def test_sum_as_string():
    try:
        from oameteringengine_rs.oameteringengine_rs import sum_as_string
    except ImportError:
        try:
            from oameteringengine_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oameteringengine_rs")
            return
            
    assert sum_as_string(1, 1) == "2"
