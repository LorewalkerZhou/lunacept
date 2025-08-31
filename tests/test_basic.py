#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : test_basic.py.py
@Author  : LorewalkerZhou
@Time    : 2025/8/24 22:41
@Desc    : 
"""
import subprocess
import sys
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def run_example(script_name: str) -> str:
    """Helper to run example script and capture output."""
    result = subprocess.run(
        [sys.executable, str(DATA_DIR / script_name)],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def test_single_line_error():
    output = run_example("single_line_error.py")

    assert "single_line_error()" in output
    assert "single_line_error.py" in output

    assert "    result = a / b" in output

    assert re.search(r"line 6, cols 13-18", output)

    assert "a = 42" in output
    assert "b = 0" in output


def test_multi_line_error():
    output = run_example("multi_line_error.py")

    assert "multi_line_error()" in output
    assert "multi_line_error.py" in output

    assert "    result = a /\\" in output
    assert "             b # multi-line ZeroDivisionError" in output

    assert re.search(r"lines 6-7, cols 13-14", output)

    assert "a = 42" in output
    assert "b = 0" in output