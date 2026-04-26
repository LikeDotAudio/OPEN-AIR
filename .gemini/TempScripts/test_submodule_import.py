try:
    import oaRustCore
    print(f"✅ oaRustCore imported. Attributes: {dir(oaRustCore)}")

    try:
        from oaRustCore import oa_logging_gate_rs
        print("✅ from oaRustCore import oa_logging_gate_rs worked")
    except ImportError as e:
        print(f"❌ from oaRustCore import oa_logging_gate_rs failed: {e}")

    try:
        from oaRustCore.oa_logging_gate_rs import is_debug_allowed
        print("✅ from oaRustCore.oa_logging_gate_rs import is_debug_allowed worked")
    except ImportError as e:
        print(f"❌ from oaRustCore.oa_logging_gate_rs import is_debug_allowed failed: {e}")

except ImportError as e:
    print(f"❌ oaRustCore import failed: {e}")
