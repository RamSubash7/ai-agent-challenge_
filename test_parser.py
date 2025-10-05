#!/usr/bin/env python3
"""
Test script for the bank statement parsers using pytest
"""

import pandas as pd
import sys
import importlib.util
from pathlib import Path
import pytest

def import_parser(parser_path):
    spec = importlib.util.spec_from_file_location("custom_parser", parser_path)
    parser_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_module)
    return parser_module

import pytest

@pytest.mark.parametrize("parser_path,pdf_path,csv_path", [
    ("custom_parser/icici_parser.py", "data/icici/icici_sample.pdf", "data/icici/icici_sample.csv"),
])
def test_bank_parser(parser_path, pdf_path, csv_path):
    assert Path(parser_path).exists(), f"Parser file not found: {parser_path}"
    assert Path(pdf_path).exists(), f"PDF file not found: {pdf_path}"
    assert Path(csv_path).exists(), f"CSV file not found: {csv_path}"
    expected_df = pd.read_csv(csv_path)
    parser_module = import_parser(parser_path)
    actual_df = parser_module.parse(pdf_path)
    assert isinstance(actual_df, pd.DataFrame), f"Expected DataFrame, got {type(actual_df)}"
    assert list(actual_df.columns) == list(expected_df.columns), f"Column mismatch: expected {list(expected_df.columns)}, got {list(actual_df.columns)}"
    assert actual_df.shape == expected_df.shape, f"Shape mismatch: expected {expected_df.shape}, got {actual_df.shape}"
    for col in expected_df.columns:
        assert actual_df[col].dtype == expected_df[col].dtype, f"Data type mismatch for column {col}: expected {expected_df[col].dtype}, got {actual_df[col].dtype}"
    assert expected_df.equals(actual_df), "Parser output does not match expected CSV via DataFrame.equals"

@pytest.mark.parametrize("parser_path", [
    "custom_parser/icici_parser.py",
])
def test_parser_contract(parser_path):
    parser_module = import_parser(parser_path)
    assert hasattr(parser_module, 'parse'), "Parser module must have a 'parse' function"
    import inspect
    sig = inspect.signature(parser_module.parse)
    assert len(sig.parameters) == 1, "parse() function must take exactly one parameter"
    param_name = list(sig.parameters.keys())[0]
    assert 'pdf' in param_name.lower() or 'path' in param_name.lower(), "Parameter should be pdf_path or similar"

if __name__ == "__main__":
    try:
        print("="*40)
        print("Running bank parser test...")
        test_bank_parser("custom_parser/icici_parser.py", "data/icici/icici_sample.pdf", "data/icici/icici_sample.csv")
        print("Bank parser test completed.")
        print("-"*40)
        print("Checking parser contract...")
        test_parser_contract("custom_parser/icici_parser.py")
        print("Contract test completed.")
        print("="*40)
        print("RESULT: All tests PASSED.")
    except Exception as e:
        print("="*40)
        print("RESULT: TEST FAILED")
        print(f"Reason: {e}")
        print("="*40)
        sys.exit(1)