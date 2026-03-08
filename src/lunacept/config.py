#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : config.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 19:57
@Desc    : 
"""
from typing import Optional

ENABLE_COLORS = True
MAX_TRACE_DEPTH = 10
MAX_VALUE_LENGTH = 100
MAX_VALUE_DEPTH = 2
GLOBAL_INSTALL = True

def configure(
    *,
    colors: Optional[bool]=None,
    max_trace_depth: Optional[int]=None,
    max_value_len: Optional[int]=None,
    max_value_depth: Optional[int]=None,
    global_install: Optional[bool]=None,
):
    """
    Configure lunacept output style.

    Args:
        colors: Whether to enable colored output (default: True)
        max_trace_depth: Maximum number of stack frames to display (default: 10)
        max_value_len: Maximum string length when printing variable values (default: 100)
        max_value_depth: Maximum recursive depth when formatting complex values (default: 2)
    """
    global ENABLE_COLORS, MAX_TRACE_DEPTH, MAX_VALUE_LENGTH, MAX_VALUE_DEPTH, GLOBAL_INSTALL

    if colors is not None:
        if not isinstance(colors, bool):
            raise TypeError(f"colors must be a bool, got {type(colors).__name__}")
        ENABLE_COLORS = colors

    if max_trace_depth is not None:
        if not isinstance(max_trace_depth, int) or max_trace_depth <= 0:
            raise ValueError(f"max_trace_depth must be a positive integer, got {max_trace_depth!r}")
        MAX_TRACE_DEPTH = max_trace_depth

    if max_value_len is not None:
        if not isinstance(max_value_len, int) or max_value_len <= 0:
            raise ValueError(f"max_value_len must be a positive integer, got {max_value_len!r}")
        MAX_VALUE_LENGTH = max_value_len

    if max_value_depth is not None:
        if not isinstance(max_value_depth, int) or max_value_depth < 0:
            raise ValueError(f"max_value_depth must be a non-negative integer, got {max_value_depth!r}")
        MAX_VALUE_DEPTH = max_value_depth

    if global_install is not None:
        if not isinstance(global_install, bool):
            raise TypeError(f"global_install must be a bool, got {type(global_install).__name__}")
        GLOBAL_INSTALL = global_install