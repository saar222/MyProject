# -*- coding: utf-8 -*-
"""
Created on Mon Aug 18 23:50:52 2025
@author: user

This module implements various statistical tests for evaluating the randomness 
of bit sequences. It provides functions to convert numbers to binary, 
perform frequency and runs tests, chi-squared tests on groups and patterns, 
autocorrelation checks, Poker test, and Maurer's Universal statistical test.

Suitable for analyzing output of pseudo-random and hardware random generators.
"""

import os
import logging

# Project folders and files for logging and results.
project_dir = r'C:\Users\user\Desktop\Project'
RESULTS_FILE = os.path.join(project_dir, "results.txt")
LOG_FILE = os.path.join(project_dir, "test_errors.log")

# Configure error logging for test errors.
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s'
)

from scipy.stats import chisquare
from collections import Counter
from scipy.stats import norm

def convert_to_bits(number, max_bits=None):
    """
    Converts a (non-negative) integer to its binary string representation.
    Pads with leading zeros up to max_bits if specified.

    Args:
        number (int): The number to convert.
        max_bits (int, optional): The length of the result string.

    Returns:
        str: The binary representation.
    """
    if number < 0:
        logging.warning(f"Skipped negative number: {number}")
        return ''
    bits = bin(number)[2:]
    if max_bits is None:
        return bits
    else:
        return bits.zfill(max_bits)

def frequency_test(bits):
    """
    Performs a frequency (monobit) test on a bit sequence.
    Uses a chi-squared test to check if number of zeros/ones is statistically balanced.

    Args:
        bits (str): String of '0's and '1's.

    Returns:
        dict: Statistics including p-value and pass/fail.
    """
    try:
        observed = [bits.count('0'), bits.count('1')]
        chi2, p = chisquare(observed)
        return {
            'zeros': observed[0],
            'ones': observed[1],
            'chi2': chi2,
            'p-value': p,
            'passed': p > 0.05   # Acceptable if not significant
        }
    except Exception as e:
        logging.error(f"frequency_test failed: {e}")
        return {'error': str(e), 'passed': False}

def runs_test(bits):
    """
    Calculates the number of runs (continuous blocks of identical digits) in the sequence,
    and compares to expected number using normal approximation.

    Args:
        bits (str): Input bit string.

    Returns:
        dict: Number of runs, z-score, p-value, and pass/fail.
    """
    try:
        n = len(bits)
        runs = 1 if n > 0 else 0
        for i in range(1, n):
            if bits[i] != bits[i-1]:
                runs += 1
        n0 = bits.count('0')
        n1 = bits.count('1')
        expected_runs = ((2 * n0 * n1) / n) + 1 if n > 0 else 0
        variance = ((2 * n0 * n1) * (2 * n0 * n1 - n)) / (n**2 * (n - 1)) if n > 1 else 0
        z = (runs - expected_runs) / (variance ** 0.5) if variance > 0 else 0
        passed = abs(z) < 1.96       # Accept if within 95% confidence
        return {
            'runs': runs,
            'expected_runs': expected_runs,
            'z-value': z,
            'passed': passed,
            'n0': n0,
            'n1': n1
        }
    except Exception as e:
        logging.error(f"runs_test failed: {e}")
        return {'error': str(e), 'passed': False}

def chi_squared_full_test(bits, group_size=8):
    """
    Splits bit sequence into groups (default of 8, i.e., bytes), 
    counts occurrences of each possible value, and does chi-squared test
    to check for uniformity.

    Args:
        bits (str): Bit string.
        group_size (int): Number of bits per group.

    Returns:
        dict: Chi-squared statistics and pass/fail.
    """
    try:
        groups = [''.join(bits[i:i+group_size]) for i in range(0, len(bits) - group_size + 1, group_size)]
        valid_groups = [grp for grp in groups if set(grp) <= {'0', '1'} and len(grp) == group_size]
        values = [int(grp, 2) for grp in valid_groups]
        counter = Counter(values)
        N = len(values)
        possible_values = 2 ** group_size
        expected_count = N / possible_values
        observed = [counter.get(i, 0) for i in range(possible_values)]
        expected = [expected_count] * possible_values
        obs_sum = sum(observed)
        exp_sum = sum(expected)
        if abs(obs_sum - exp_sum) > 1e-8:
            expected = [e * (obs_sum / exp_sum) for e in expected]
        chi2, p = chisquare(observed, f_exp=expected)
        return {
            'chi2': chi2,
            'p-value': p,
            'passed': p > 0.05,
            'group_size': group_size,
            'N': N,
            'observed_nonzero': sum(1 for x in observed if x > 0)
        }
    except Exception as e:
        logging.error(f"chi_squared_full_test failed: {e}")
        return {'error': str(e), 'passed': False}

def serial_test(bits, group_size=2):
    """
    Counts all possible bit patterns of length 'group_size' in the sequence,
    performs chi-squared test for pattern uniformity.

    Args:
        bits (str): Bit string.
        group_size (int): Length of each pattern.

    Returns:
        dict: Statistics for pattern frequencies and test result.
    """
    try:
        n = len(bits)
        groups = [''.join(bits[i:i+group_size]) for i in range(n - group_size + 1)]
        counter = Counter(groups)
        N = len(groups)
        patterns = [''.join(f'{i:0{group_size}b}') for i in range(2 ** group_size)]
        observed = [counter.get(pat, 0) for pat in patterns]
        expected = [N / len(patterns)] * len(patterns)
        obs_sum = sum(observed)
        exp_sum = sum(expected)
        if abs(obs_sum - exp_sum) > 1e-8:
            expected = [e * (obs_sum / exp_sum) for e in expected]
        chi2, p = chisquare(observed, f_exp=expected)
        return {
            'chi2': chi2,
            'p-value': p,
            'passed': p > 0.05,
            'N': N,
            'group_size': group_size,
            'pattern_counts': dict(zip(patterns, observed))
        }
    except Exception as e:
        logging.error(f"serial_test failed: {e}")
        return {'error': str(e), 'passed': False}

def autocorrelation_test(bits, lag=1):
    """
    Calculates autocorrelation coefficient at given lag
    - checks how much bits are related to bits lag positions later.
    Near zero shows low dependency.

    Args:
        bits (str): Bit string.
        lag (int): Lag (how many ahead).

    Returns:
        dict: Autocorrelation coefficient (r), z-score, p-value, and pass/fail.
    """
    try:
        n = len(bits)
        if n <= lag:
            return {"error": "Sequence too short to perform autocorrelation at this lag"}
        bit_nums = [int(b) for b in bits]
        mean = sum(bit_nums) / n
        num = sum((bit_nums[i] - mean) * (bit_nums[i + lag] - mean) for i in range(n - lag))
        denom = sum((bit_nums[i] - mean) ** 2 for i in range(n))
        r = num / denom if denom != 0 else 0
        z = r * ((n - lag) ** 0.5)
        p_val = 2 * (1 - norm.cdf(abs(z)))
        passed = abs(r) < 0.05  # Accept if weak autocorrelation
        return {
            "autocorrelation": r,
            "lag": lag,
            "z": z,
            "p-value": p_val,
            "passed": passed,
            "n": n
        }
    except Exception as e:
        logging.error(f"autocorrelation_test failed: {e}")
        return {'error': str(e), 'passed': False}

def poker_test(bits, group_size=4):
    """
    Splits bit sequence into groups (of size group_size) and checks 
    the distribution of group patterns (as poker hands analogy).
    Uses chi-squared test for uniformity.

    Args:
        bits (str): Bit string.
        group_size (int): Bits per group (hand).

    Returns:
        dict: Statistics and test result.
    """
    try:
        n = len(bits)
        num_groups = n // group_size
        if num_groups == 0:
            return {"error": "Sequence too short for the Poker test"}
        groups = [''.join(bits[i*group_size:(i+1)*group_size]) for i in range(num_groups)]
        patterns = [''.join(f'{i:0{group_size}b}') for i in range(2**group_size)]
        counter = Counter(groups)
        observed = [counter.get(pat, 0) for pat in patterns]
        expected = [num_groups / len(patterns)] * len(patterns)
        chi2, p = chisquare(observed, f_exp=expected)
        return {
            'chi2': chi2,
            'p-value': p,
            'passed': p > 0.05,
            'num_groups': num_groups,
            'group_size': group_size,
            'pattern_counts': dict(zip(patterns, observed))
        }
    except Exception as e:
        logging.error(f"poker_test failed: {e}")
        return {'error': str(e), 'passed': False}

import math

def maurer_universal_test(bits, L=7):
    """
    Maurer's Universal Statistical Test estimates the compressibility 
    (unpredictability) of the sequence. Needs very long sequence. 
    Suitable for strong randomness checks.

    Args:
        bits (str or list): Bit string or list.
        L (int): Block length to use.

    Returns:
        dict: Test values and result.
    """
    try:
        n = len(bits)
        if n < 1010:
            return {"error": "Sequence too short (less than 1010 bits)"}
        Q = 10 * (2 ** L)
        K = n // L - Q
        if K <= 0:
            return {"error": f"Not enough bits (L={L}, Q={Q}, groups={K})"}
        if isinstance(bits, list):
            bits = ''.join(bits)
        blocks = [bits[i * L:(i + 1) * L] for i in range((n)//L)]
        T = {k: 0 for k in range(2**L)}
        for i in range(Q):
            key = int(blocks[i], 2)
            T[key] = i + 1
        sum_logs = 0
        for i in range(Q, Q + K):
            key = int(blocks[i], 2)
            d = i + 1 - T.get(key, 0)
            sum_logs += math.log2(d)
            T[key] = i + 1
        fn = sum_logs / K
        expected = _maurer_expected_value(L)
        variance = _maurer_variance(L)
        sigma = math.sqrt(variance / K)
        z = (fn - expected) / sigma
        p_value = 2 * (1 - norm.cdf(abs(z)))
        return {
            "fn": fn,
            "expected": expected,
            "z": z,
            "p-value": p_value,
            "passed": p_value > 0.01,
            "L": L,
            "Q": Q,
            "K": K,
            "n": n
        }
    except Exception as e:
        logging.error(f"maurer_universal_test failed: {e}")
        return {'error': str(e), 'passed': False}

def _maurer_expected_value(L):
    """
    Expected values for Maurer Universal Test, for block size L.
    """
    expected_table = {
        6: 5.2177052, 7: 6.1962507, 8: 7.1836656, 9: 8.1764248,
        10: 9.1723243, 11: 10.170032, 12: 11.168765,
        13: 12.168070, 14: 13.167693, 15: 14.167488, 16: 15.167379
    }
    return expected_table.get(L, 0)

def _maurer_variance(L):
    """
    Variance values for Maurer Universal Test, for block size L.
    """
    variance_table = {
        6: 2.954, 7: 3.125, 8: 3.238, 9: 3.311,
        10: 3.356, 11: 3.384, 12: 3.401,
        13: 3.410, 14: 3.416, 15: 3.419, 16: 3.421
    }
    return variance_table.get(L, 1)
