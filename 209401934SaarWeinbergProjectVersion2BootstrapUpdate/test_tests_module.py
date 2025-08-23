# -*- coding: utf-8 -*-
"""
Created on Thu Aug 21 00:18:59 2025

@author: user
"""

import pytest
import tests_module

# Test frequency_test: Checks correct counting of '0' and '1' bits and statistical result
def test_frequency_test_balanced():
    bits = "0101010101"  # 5 zeros, 5 ones
    result = tests_module.frequency_test(bits)
    assert result['zeros'] == 5
    assert result['ones'] == 5
    assert 'p-value' in result
    assert result['passed'] ==True or result['passed']==False 

def test_frequency_test_all_zeros():
    bits = "00000"
    result = tests_module.frequency_test(bits)
    assert result['zeros'] == 5
    assert result['ones'] == 0
    assert not result['passed']

# Test runs_test: Checks number of runs and calculations
def test_runs_test_simple():
    bits = "010101"  # alternate, should have 6 runs
    result = tests_module.runs_test(bits)
    assert result['runs'] == 6
    assert result['n0'] == 3
    assert result['n1'] == 3
    assert isinstance(result['expected_runs'], float)

def test_runs_test_single_run():
    bits = "111111"
    result = tests_module.runs_test(bits)
    assert result['runs'] == 1
    assert result['n1'] == 6
    assert result['n0'] == 0

# Test chi_squared_full_test: Validates distribution within bytes/patterns
def test_chi_squared_full_test():
    bits = "0110100011010001" * 4  # 8-bit groups (repeated patterns)
    result = tests_module.chi_squared_full_test(bits, group_size=8)
    assert 'chi2' in result
    assert 'p-value' in result
    assert isinstance(result['N'], int)
    assert result['passed'] ==True or result['passed']==False 

# Test serial_test: Validates serial pattern counts and chi-square for pairs
def test_serial_test_pairs():
    bits = "001100110011"  # Expect patterns "00", "01", "11", "10" to be present
    result = tests_module.serial_test(bits, group_size=2)
    assert 'chi2' in result
    assert 'p-value' in result
    assert all(pat in result['pattern_counts'] for pat in ["00", "01", "10", "11"])

# Test autocorrelation_test: Checks computation of autocorrelation coefficient
def test_autocorrelation_test_no_corr():
    bits = "01010101"  # Highly alternating, expect low autocorrelation at lag=1
    result = tests_module.autocorrelation_test(bits, lag=1)
    assert 'autocorrelation' in result
    assert isinstance(result['autocorrelation'], float)
    assert 'passed' in result

def test_autocorrelation_test_short_sequence():
    bits = "01"
    result = tests_module.autocorrelation_test(bits, lag=2)
    assert 'error' in result

# Test poker_test: Checks counting of poker hands in given groups
def test_poker_test_group_4():
    bits = "0100011101000111"  # two groups of four bits
    result = tests_module.poker_test(bits, group_size=4)
    assert 'chi2' in result
    assert 'p-value' in result
    assert result['num_groups'] == 4

def test_poker_test_too_short():
    bits = "01"
    result = tests_module.poker_test(bits, group_size=4)
    assert 'error' in result

# Test maurer_universal_test: Checks result and error for short sequence
def test_maurer_universal_test_short():
    bits = "01" * 100  # insufficient for L=7 (1010 bits needed)
    result = tests_module.maurer_universal_test(bits, L=7)
    assert 'error' in result

def test_maurer_universal_test_valid():
    # A random long enough sequence for L=7 (minimum n=1010 bits)
    bits = "01001101" * 1750  # 8 bits × 1750 = 14,000 bits (>Q*L)
    result = tests_module.maurer_universal_test(bits, L=7)
    assert 'fn' in result
    assert 'expected' in result
    assert 'p-value' in result
    assert 'passed' in result

# Run all tests if this file is executed directly (optional)
if __name__ == "__main__":
    pytest.main(["test_tests_module.py"])
