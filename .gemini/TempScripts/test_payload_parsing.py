# .gemini/TempScripts/test_payload_parsing.py
import orjson


def original_logic(payload):
    try:
        try:
            return str(orjson.loads(payload).get("value")).lower() == "true"
        except:
            return str(payload).lower() == "true"
    except Exception as e:
        print(f"Error: {e}")
        return False

def refactored_logic(payload):
    if not payload:
        return False

    # Try parsing as JSON first
    try:
        data = orjson.loads(payload)
        if isinstance(data, dict):
            return str(data.get("value", "")).lower() == "true"
    except (orjson.JSONDecodeError, TypeError):
        pass

    # Fallback to raw string check
    return str(payload).decode('utf-8').lower() == "true" if isinstance(payload, bytes) else str(payload).lower() == "true"

test_cases = [
    (b'{"value": "true"}', True),
    (b'{"value": "false"}', False),
    (b'true', True),
    (b'false', False),
    ("true", True),
    ("false", False),
    (b'invalid json', False),
]

for p, expected in test_cases:
    res = original_logic(p)
    print(f"Payload: {p} | Expected: {expected} | Got: {res}")
    assert res == expected
