import pytest

def test_sum_as_string():
    try:
        from oastateregistry_rs.oastateregistry_rs import sum_as_string
    except ImportError:
        try:
            from oastateregistry_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oastateregistry_rs")
            return
            
    assert sum_as_string(1, 1) == "2"
