import pytest

def test_sum_as_string():
    try:
        from oaRustCore.oa_metering_engine_rs import sum_as_string
    except ImportError:
        try:
            from oaRustCore.oa_metering_engine_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oameteringengine_rs")
            return
            
    assert sum_as_string(1, 1) == "2"
