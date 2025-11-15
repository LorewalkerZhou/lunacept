#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : parse.py.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 11:49
@Desc    : 
"""
from __future__ import annotations

import _ast
import ast
import hashlib
import linecache
from dataclasses import dataclass, field
from types import FrameType
from typing import Any

@dataclass
class TraceNode:
    expr: str
    value: Any
    children: list[TraceNode] = field(default_factory=list)

@dataclass
class LunaFrame:
    frame: FrameType
    filename: str
    func_name: str
    tb_lasti: int
    display_lines: list[int]
    source_segment: str
    source_segment_before: str
    source_segment_after: str
    source_segment_pos: tuple[int, int, int, int]  # start_line, end_line, col_start, col_end
    trace_tree: list[TraceNode]

class ExprTracer(ast.NodeVisitor):
    def __init__(self, frame: FrameType, pos: tuple[int, int, int, int]):
        self.frame = frame
        self.pos = pos

    def _get_value(self, name: str) -> Any:
        if name in self.frame.f_locals:
            return self.frame.f_locals[name]
        if name in self.frame.f_globals:
            return self.frame.f_globals[name]
        return "<unknow>"

    def _hash_expr(self, node: _ast.expr) -> str:
        expr_str = ast.unparse(node)
        lineno = node.lineno
        end_lineno = node.end_lineno if node.end_lineno else lineno
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset

        lineno += self.pos[0] - 1
        end_lineno += self.pos[0] - 1

        if node.lineno == 1:
            col_offset += self.pos[2]
            end_col_offset += self.pos[2]
        ori_str = f"{expr_str}-{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"
        return hashlib.md5(ori_str.encode()).hexdigest()[0:12]

    def _resolve_tmp_value(self, node: _ast.expr | None) -> Any:
        if node is None:
            return "<unknow>"
        hash_id = self._hash_expr(node)
        tmp_name = f"__luna_tmp_{hash_id}"
        value = self._get_value(tmp_name)
        return value

    def _collect_children(self, node: ast.AST) -> list[TraceNode]:
        children: list[TraceNode] = []
        for child in ast.iter_child_nodes(node):
            result = self.visit(child)
            if not result:
                continue
            if isinstance(result, list):
                children.extend(result)
            else:
                children.append(result)
        return children

    def generic_visit(self, node):
        if isinstance(node, ast.expr):
            expr_str = ast.unparse(node)
            value = self._resolve_tmp_value(node)
            children = self._collect_children(node)
            return TraceNode(expr_str, value, children)
        return self._collect_children(node)

    def visit_Module(self, node: ast.Module):
        roots: list[TraceNode] = []
        for stmt in node.body:
            result = self.visit(stmt)
            if not result:
                continue
            if isinstance(result, list):
                roots.extend(result)
            else:
                roots.append(result)
        return roots

    def visit_Expr(self, node: ast.Expr):
        return self.visit(node.value)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            value = self._get_value(node.id)
            return TraceNode(node.id, value, [])
        return None

    def visit_Constant(self, node: ast.Constant):
        return None

    def visit_Call(self, node: ast.Call):
        children = []
        func_node = self.visit(node.func)
        if func_node:
            if isinstance(func_node, list):
                children.extend(func_node)
            else:
                children.append(func_node)
        for arg in node.args:
            child = self.visit(arg)
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)
        for kw in node.keywords:
            child = self.visit(kw.value)
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        children = [child for child in (left, right) if child]
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        children = [operand] if operand else []
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_BoolOp(self, node: ast.BoolOp):
        children = []
        for value_node in node.values:
            child = self.visit(value_node)
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_Compare(self, node: ast.Compare):
        children = []
        left_child = self.visit(node.left)
        if left_child:
            children.append(left_child)
        for comp in node.comparators:
            child = self.visit(comp)
            if child:
                children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_Attribute(self, node: ast.Attribute):
        value_node = self.visit(node.value)
        children = []
        if value_node:
            if isinstance(value_node, list):
                children.extend(value_node)
            else:
                children.append(value_node)
        expr_str = ast.unparse(node)
        # Attributes themselves are not instrumented; try resolving via parent tmp.
        resolved_value = self._resolve_tmp_value(node) if isinstance(node, ast.expr) else "<unknow>"
        return TraceNode(expr_str, resolved_value, children)

    def visit_Subscript(self, node: ast.Subscript):
        value_node = self.visit(node.value)
        slice_node = self.visit(node.slice)
        children = []
        for child in (value_node, slice_node):
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_List(self, node: ast.List):
        children = self._collect_children(node)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_Tuple(self, node: ast.Tuple):
        children = self._collect_children(node)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_Dict(self, node: ast.Dict):
        children = []
        for key, value in zip(node.keys, node.values, strict=False):
            key_child = self.visit(key) if key else None
            value_child = self.visit(value) if value else None
            for child in (key_child, value_child):
                if child:
                    if isinstance(child, list):
                        children.extend(child)
                    else:
                        children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node)
        return TraceNode(expr_str, value, children)

    def visit_Slice(self, node: ast.Slice):
        children = []
        for part in (node.lower, node.upper, node.step):
            child = self.visit(part)
            if child:
                if isinstance(child, list):
                    children.extend(child)
                else:
                    children.append(child)
        expr_str = ast.unparse(node)
        value = self._resolve_tmp_value(node if isinstance(node, ast.expr) else None)
        return TraceNode(expr_str, value, children)

def create_luna_frame(
        frame: FrameType,
        tb_lasti: int
) -> LunaFrame:
    filename = frame.f_code.co_filename
    pos_iter = frame.f_code.co_positions()

    positions = None
    for i, pos in enumerate(pos_iter):
        if i == tb_lasti // 2:  # tb_lasti is bytecode offset, divide by 2 to get instruction index
            positions = pos
            break

    start_line, end_line, col_start, col_end = positions
    if end_line is None:
        end_line = start_line

    # Get all involved lines, including one line of context before and after
    display_start = max(1, start_line - 1)
    display_end = end_line + 1

    # Get all lines in display range (only non-empty lines for display_lines)
    display_lines = []
    all_lines = []
    for l in range(display_start, display_end + 1):
        line = linecache.getline(filename, l)
        if line.strip():
            display_lines.append(l)
        all_lines.append((l, line.rstrip()))
    
    # Build complete text and apply column-based segmentation
    complete_text_lines = [line_content for line_num, line_content in all_lines]
    complete_text = '\n'.join(complete_text_lines)
    
    # Find absolute positions for cutting
    line_start_positions = []
    current_pos = 0
    for line_num, line_content in all_lines:
        line_start_positions.append((line_num, current_pos))
        current_pos += len(line_content) + 1  # +1 for newline
    
    # Find start and end absolute positions
    start_abs_pos = None
    end_abs_pos = None
    
    for line_num, line_start_pos in line_start_positions:
        if line_num == start_line:
            start_abs_pos = line_start_pos + (col_start if col_start is not None else 0)
        if line_num == end_line:
            end_abs_pos = line_start_pos + (col_end if col_end is not None else len(complete_text_lines[line_num - display_start]))
    
    # Extract the three segments
    if start_abs_pos is not None and end_abs_pos is not None:
        source_segment_before = complete_text[:start_abs_pos]
        source_segment = complete_text[start_abs_pos:end_abs_pos]
        source_segment_after = complete_text[end_abs_pos:]
    else:
        # Fallback
        source_segment_before = ""
        source_segment = complete_text
        source_segment_after = ""

    source_segment_pos = (start_line, end_line, col_start, col_end)
    trace_tree = build_trace_tree(frame, source_segment, source_segment_pos)
    return LunaFrame(
        frame=frame,
        filename = frame.f_code.co_filename,
        func_name = frame.f_code.co_name,
        tb_lasti = tb_lasti,
        display_lines = display_lines,
        source_segment = source_segment,
        source_segment_before = source_segment_before,
        source_segment_after = source_segment_after,
        source_segment_pos = source_segment_pos,
        trace_tree=trace_tree
    )

def build_trace_tree(
        frame: FrameType,
        source_line: str,
        pos: tuple[int, int, int, int]
) -> list[TraceNode]:
    """Parse source code and build expression tree with evaluated values."""
    try:
        tree = ast.parse(source_line, mode='exec')
    except Exception:
        return []

    tracer = ExprTracer(frame, pos)
    result = tracer.visit(tree)

    if not result:
        return []

    if isinstance(result, TraceNode):
        roots = [result]
    else:
        roots = list(result)

    if len(roots) == 1 and roots[0].children:
        node = roots[0]
        if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
            return node.children

    return roots

def collect_frames(exc_traceback):
    tb = exc_traceback
    frame_list = []
    from .config import MAX_TRACE_DEPTH
    while tb:
        frame = tb.tb_frame
        luna_frame = create_luna_frame(frame, tb.tb_lasti)
        frame_list.append(luna_frame)
        tb = tb.tb_next
    if len(frame_list) > MAX_TRACE_DEPTH:
        skip = len(frame_list) - MAX_TRACE_DEPTH
        frame_list = frame_list[skip:]
    return frame_list