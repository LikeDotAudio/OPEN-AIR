import pytest

def test_sum_as_string():
    try:
        from oaRustCore.oa_core_router_rs import sum_as_string
    except ImportError:
        try:
            from oaRustCore.oa_core_router_rs import sum_as_string
        except ImportError:
            pytest.skip("sum_as_string not found in oacorerouter_rs")
            return
            
    assert sum_as_string(1, 1) == "2"

def test_core_router():
    from oaRustCore import oa_core_router_rs as oacorerouter_rs
    
    # Check where CoreRouter is located
    CoreRouter = getattr(oacorerouter_rs, "CoreRouter", None)
    if CoreRouter is None and hasattr(oacorerouter_rs, "oacorerouter_rs"):
        CoreRouter = getattr(oacorerouter_rs.oacorerouter_rs, "CoreRouter", None)
        
    if CoreRouter is None:
        pytest.skip("CoreRouter class not found")
        return

    # Test the main functionality of the CoreRouter class
    router = CoreRouter()
    
    # Test inbound queue
    test_message = {"topic": "test/inbound", "value": 100}
    router.push_inbound(test_message)
    assert router.inbound_len() == 1
    
    received = router.pop_inbound()
    assert received == test_message
    assert router.inbound_len() == 0
    
    # Test outbound queue
    test_out = {"topic": "test/outbound", "value": 200}
    router.push_outbound(test_out)
    assert router.outbound_len() == 1
    
    received_out = router.pop_outbound()
    assert received_out == test_out
    assert router.outbound_len() == 0

def test_empty_pops():
    from oaRustCore import oa_core_router_rs as oacorerouter_rs
    
    # Check where CoreRouter is located
    CoreRouter = getattr(oacorerouter_rs, "CoreRouter", None)
    if CoreRouter is None and hasattr(oacorerouter_rs, "oacorerouter_rs"):
        CoreRouter = getattr(oacorerouter_rs.oacorerouter_rs, "CoreRouter", None)
        
    if CoreRouter is None:
        pytest.skip("CoreRouter class not found")
        return

    router = CoreRouter()
    assert router.pop_inbound() is None
    assert router.pop_outbound() is None
