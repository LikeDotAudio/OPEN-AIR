import pytest


def test_sum_as_string():
    try:
        from oaRustCore.oa_csv_parser_rs import sum_as_string
    except ImportError:
        try:
            from oaRustCore.oa_csv_parser_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oacsvparser_rs")
            return

    assert sum_as_string(1, 1) == "2"
