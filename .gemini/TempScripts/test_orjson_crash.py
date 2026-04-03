
import orjson
import sys

def test_orjson_recursion():
    print("Testing orjson with self-referencing dictionary...")
    d = {"a": 1}
    d["self"] = d
    
    try:
        # orjson.dumps(d) should raise an exception or crash
        print("Attempting orjson.dumps(d)...")
        result = orjson.dumps(d)
        print("Success?")
    except Exception as e:
        print(f"Caught expected exception: {e}")
    except BaseException as e:
        print(f"Caught base exception: {type(e)}")

if __name__ == "__main__":
    test_orjson_recursion()
