# -*- coding: utf-8 -*-
import pytest
from generators import (
    PythonRandomGenerator, 
    JavaRandomGenerator, 
    NanoTimeRandomGenerator, 
    SoundRandomGenerator,
    generator_factory
)

# Test for PythonRandomGenerator: 
# Ensures 100 generated values are in the requested range [0, 10].
def test_python_random_generator_in_range():
    rng = PythonRandomGenerator()
    results = [rng.generate(10) for _ in range(100)]
    for val in results:
        assert 0 <= val <= 10

# Test for PythonRandomGenerator: 
# Ensures several generated values are not all identical (basic randomness check).
def test_python_random_generator_different_values():
    rng = PythonRandomGenerator()
    vals = set(rng.generate(1000) for _ in range(50))
    assert len(vals) > 1

# Test for NanoTimeRandomGenerator: 
# Ensures all generated values are in the requested range [0, 999999].
def test_nanotime_random_generator_range():
    rng = NanoTimeRandomGenerator()
    for _ in range(30):
        val = rng.generate(999999)
        assert 0 <= val <= 999999

# Test for JavaRandomGenerator: 
# Uses monkeypatch to simulate valid output for safe_run.
# Checks the returned value is an int and equals 42.
def test_java_random_generator_returns_int(monkeypatch):
    rng = JavaRandomGenerator()
    import generators
    # Monkeypatch safe_run to always return "42\n"
    monkeypatch.setattr(generators, 'safe_run', lambda *a, **k: "42\n")
    val = rng.generate(123)
    assert type(val) is int and val == 42

# Test for JavaRandomGenerator: 
# Uses monkeypatch to simulate an error output for safe_run.
# Checks the returned value is 0 if the output is invalid.
def test_java_random_generator_returns_zero_on_error(monkeypatch):
    rng = JavaRandomGenerator()
    import generators
    # Monkeypatch safe_run to always return an error string
    monkeypatch.setattr(generators, 'safe_run', lambda *a, **k: "error_string")
    val = rng.generate(10)
    assert val == 0

# Test for SoundRandomGenerator:
# Checks that SoundRandomGenerator can be created and closed without raising exceptions.
def test_sound_random_generator_close():
    rng = SoundRandomGenerator()
    # Does not verify sound sampling (needs hardware),
    # only tests correct creation and closure of the object
    rng.close()
    assert True  # Passed if no exception occurs

# Tests for generator_factory function:
# Each test verifies that generator_factory returns the correct type for a valid name.
def test_generator_factory_python_random():
    gen = generator_factory('pythonrand')
    assert isinstance(gen, PythonRandomGenerator)

def test_generator_factory_nanotime():
    gen = generator_factory('time')
    assert isinstance(gen, NanoTimeRandomGenerator)

def test_generator_factory_java():
    gen = generator_factory('javathreads')
    assert isinstance(gen, JavaRandomGenerator)

def test_generator_factory_sound():
    gen = generator_factory('sound')
    assert isinstance(gen, SoundRandomGenerator)

# Test for generator_factory with an invalid name:
# Ensures ValueError is raised for unknown generators.
def test_generator_factory_unknown_raises():
    import generators
    with pytest.raises(ValueError):
        generators.generator_factory('doesnotexist')

# This line runs pytest programmatically
pytest.main(["test_generators.py"])
