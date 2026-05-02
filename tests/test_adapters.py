# The Pria Project
# Adapter Tests — test_adapters.py
# Tests the base interface and mock adapter.
# Ollama adapter is tested only if Ollama is running.

import sys
sys.path.append("C:\\pria")

from adapters.base import BaseAdapter
from adapters.mock import MockAdapter
from adapters.ollama import OllamaAdapter

passed = 0
failed = 0

def check(label: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1

print("\n─── PRIA ADAPTER TEST RESULTS ──────────────────────────────────\n")

# Test 1 — Base adapter raises errors on unimplemented methods
print("1. Base adapter interface enforcement")
base = BaseAdapter()
try:
    base.complete("test")
    check("complete() should have raised NotImplementedError", False)
except NotImplementedError:
    check("complete() raises NotImplementedError", True)

try:
    base.is_available()
    check("is_available() should have raised NotImplementedError", False)
except NotImplementedError:
    check("is_available() raises NotImplementedError", True)

try:
    base.get_model_name()
    check("get_model_name() should have raised NotImplementedError", False)
except NotImplementedError:
    check("get_model_name() raises NotImplementedError", True)

# Test 2 — Mock adapter basic behavior
print("\n2. Mock adapter basic behavior")
mock = MockAdapter(model_name="test-model")
check("Mock is always available", mock.is_available() == True)
check("Mock returns configured model name", mock.get_model_name() == "test-model")

response = mock.complete("hello")
check("Mock returns a response string", isinstance(response, str))
check("Mock response is not empty", len(response) > 0)

# Test 3 — Mock call counting
print("\n3. Mock call counting")
mock.reset()
mock.complete("first")
mock.complete("second")
mock.complete("third")
check("Call count is 3 after three completions", mock.get_call_count() == 3)
mock.reset()
check("Call count resets to 0", mock.get_call_count() == 0)

# Test 4 — Mock scripted responses
print("\n4. Mock scripted responses")
scripted = MockAdapter(responses=["first response", "second response", "third response"])
check("First call returns first response", scripted.complete("a") == "first response")
check("Second call returns second response", scripted.complete("b") == "second response")
check("Third call returns third response", scripted.complete("c") == "third response")
check("Fourth call returns last response when list exhausted", 
      scripted.complete("d") == "third response")

# Test 5 — Mock adapter inherits from BaseAdapter
print("\n5. Inheritance")
check("MockAdapter is instance of BaseAdapter", isinstance(mock, BaseAdapter))
ollama = OllamaAdapter()
check("OllamaAdapter is instance of BaseAdapter", isinstance(ollama, BaseAdapter))

# Test 6 — Ollama adapter availability check
print("\n6. Ollama adapter")
ollama = OllamaAdapter(model="dolphin3-3b")
available = ollama.is_available()
if available:
    print("  [INFO] Ollama is running — testing live completion")
    response = ollama.complete("Say the word hello and nothing else.")
    check("Ollama returns a non-empty response", len(response) > 0)
    check("Ollama model name is set", len(ollama.get_model_name()) > 0)
else:
    print("  [INFO] Ollama is not running — skipping live tests")
    print("  [INFO] This is expected if Ollama is not installed yet")
    check("Ollama reports unavailable cleanly", available == False)

print(f"\n─── {passed} passed, {failed} failed ───────────────────────────────────\n")