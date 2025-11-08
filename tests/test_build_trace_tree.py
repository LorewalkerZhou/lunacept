#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : test_build_trace_tree.py
@Author  : LorewalkerZhou
@Time    : 2025/11/8 17:55
@Desc    : 
"""
import ast
import types

import pytest
from lunacept.parse import build_trace_tree, TraceNode

def trace_tree_to_structure(nodes: list[TraceNode]) -> list[dict]:
    """Convert TraceNode tree into comparable structure of expressions only."""
    structure = []
    for node in nodes:
        node_struct = {
            "expr": node.expr,
            "children": trace_tree_to_structure(node.children),
        }
        structure.append(node_struct)
    return structure

def test_simple_binop_structure():
    code = "a + f(b)"
    fake_frame = types.SimpleNamespace(
        f_locals={"a": 1, "b": 2, "f": lambda x: x},
        f_globals={}
    )
    pos = (1, 0, 0, len(code))

    tree_nodes = build_trace_tree(fake_frame, code, pos)

    structure = trace_tree_to_structure(tree_nodes)

    expected = [
        {"expr": "a", "children": []},
            {
                "expr": "f(b)",
                "children": [
                    {"expr": "f", "children": []},
                    {"expr": "b", "children": []},
                ]
            }
        ]

    assert structure == expected
