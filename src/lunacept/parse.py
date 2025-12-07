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
import inspect
import textwrap
import functools
import hashlib
import linecache
from dataclasses import dataclass, field
from types import FrameType, CodeType
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

    def _hash_expr(self, expr_str: str, node: _ast.expr) -> str:
        """
        Calculate hash for an expression node.
        Must match Instrumentor._make_temp_var exactly.
        """
        lineno = node.lineno
        end_lineno = node.end_lineno if node.end_lineno else lineno
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset

        lineno += self.pos[0] - 1
        end_lineno += self.pos[0] - 1

        # Adjust col_offset if source_segment doesn't start at column 0
        if node.lineno == 1 and self.pos[2] is not None and self.pos[2] > 0:
            col_offset = (col_offset if col_offset is not None else 0) + self.pos[2]
            if end_col_offset is not None:
                end_col_offset = end_col_offset + self.pos[2]
        
        col_offset = col_offset if col_offset is not None else 0
        end_col_offset = end_col_offset if end_col_offset is not None else col_offset
        
        ori_str = f"{expr_str}-{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"
        return hashlib.md5(ori_str.encode()).hexdigest()[0:12]

    def _get_value(self, name: str) -> Any:
        if name in self.frame.f_locals:
            return self.frame.f_locals[name]
        if name in self.frame.f_globals:
            return self.frame.f_globals[name]
        if name in self.frame.f_builtins:
            return self.frame.f_builtins[name]
        return "<unknown>"

    def _resolve_value(self, expr_str: str, node: _ast.expr) -> Any:
        hash_id = self._hash_expr(expr_str, node)
        tmp_name = f"__luna_tmp_{hash_id}"
        
        # Temporary variables are always in locals
        if tmp_name in self.frame.f_locals:
            return self.frame.f_locals[tmp_name]

        return "<unknown>"

    def _trace_expr(self, node: ast.AST) -> TraceNode:
        expr_str = ast.unparse(node)
        children = self.generic_visit(node)
        if hasattr(node, "ctx") and not isinstance(node.ctx, ast.Load):
            value = "<left value>"
        else:
            value = self._resolve_value(expr_str, node)

        return TraceNode(expr_str, value, children)

    def generic_visit(self, node):
        children = []
        for child in ast.iter_child_nodes(node):
            result = self.visit(child)
            if result is None:
                continue
            if isinstance(result, list):
                children.extend(result)
            else:
                children.append(result)
        return children

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            value = self._get_value(node.id)
            return TraceNode(node.id, value, [])
        return []

    def visit_Constant(self, node: ast.Constant):
        return []

    def visit_Call(self, node: ast.Call):
        return self._trace_expr(node)

    def visit_BinOp(self, node: ast.BinOp):
        return self._trace_expr(node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        return self._trace_expr(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        return self._trace_expr(node)

    def visit_Compare(self, node: ast.Compare):
        return self._trace_expr(node)

    def visit_Attribute(self, node: ast.Attribute):
        return self._trace_expr(node)

    def visit_Subscript(self, node: ast.Subscript):
        return self._trace_expr(node)

    def visit_Assign(self, node: ast.Assign):
        expr_str = ast.unparse(node)
        value = "<assign stmt>"
        children = []
        for target_node in node.targets:
            target_node = self.visit(target_node)
            if target_node:
                if isinstance(target_node, list):
                    children.extend(target_node)
                else:
                    children.append(target_node)

        value_node = self.visit(node.value)
        if value_node:
            if isinstance(value_node, list):
                children.extend(value_node)
            else:
                children.append(value_node)

        return TraceNode(expr_str, value, children)

    def visit_AugAssign(self, node: ast.AugAssign):
        expr_str = ast.unparse(node)
        value = "<augassign stmt>"
        children = []
        target_node = self.visit(node.target)
        if target_node:
            if isinstance(target_node, list):
                children.extend(target_node)
            else:
                children.append(target_node)

        value_node = self.visit(node.value)
        if value_node:
            if isinstance(value_node, list):
                children.extend(value_node)
            else:
                children.append(value_node)

        return TraceNode(expr_str, value, children)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        expr_str = ast.unparse(node)
        value = "<annassign stmt>"
        children = []
        target_node = self.visit(node.target)
        if target_node:
             if isinstance(target_node, list):
                 children.extend(target_node)
             else:
                 children.append(target_node)

        if node.value:
            value_node = self.visit(node.value)
            if value_node:
                if isinstance(value_node, list):
                    children.extend(value_node)
                else:
                    children.append(value_node)

        return TraceNode(expr_str, value, children)

    def visit_List(self, node: ast.List):
        return self._trace_expr(node)

    def visit_Tuple(self, node: ast.Tuple):
        return self._trace_expr(node)

    def visit_Dict(self, node: ast.Dict):
        return self._trace_expr(node)

    def visit_Set(self, node: ast.Set):
        return self._trace_expr(node)
    
    def visit_ListComp(self, node: ast.ListComp):
        return self._trace_expr(node)

    def visit_SetComp(self, node: ast.SetComp):
        return self._trace_expr(node)

    def visit_DictComp(self, node: ast.DictComp):
        return self._trace_expr(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        return self._trace_expr(node)
    
    def visit_IfExp(self, node: ast.IfExp):
        return self._trace_expr(node)
    
    def visit_Lambda(self, node: ast.Lambda):
        expr_str = ast.unparse(node)
        value = self._resolve_value(expr_str, node)
        return TraceNode(expr_str, value, [])

    def visit_NamedExpr(self, node: ast.NamedExpr):
        return self._trace_expr(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        return self._trace_expr(node)

def _find_search_node(
        tree: ast.AST,
        start_line: int,
        end_line: int,
        col_start: int,
        col_end: int
) -> ast.AST | None:
    """
    Find the AST node that matches the given position range.
    """
    for node in ast.walk(tree):
        if not isinstance(node, (ast.expr, ast.stmt)):
            continue
            
        if not hasattr(node, 'lineno'):
            continue
            
        n_start_line = node.lineno
        n_end_line = getattr(node, 'end_lineno', n_start_line)
        n_col_offset = node.col_offset
        n_end_col_offset = getattr(node, 'end_col_offset', None)
        
        if (n_start_line == start_line and 
            n_end_line == end_line and 
            n_col_offset == col_start and 
            n_end_col_offset == col_end):
            return node
            
    return None

def _split_source_code(
    filename: str,
    start_line: int,
    end_line: int,
    col_start: int,
    col_end: int
) -> tuple[str, str, str, list[int]]:
    """
    Split source code into three segments: before, segment, and after.
    """
    # Get all involved lines, including one line of context before and after
    display_start = max(1, start_line - 1)
    display_end = end_line + 1

    # Get all lines in display range (only non-empty lines for display_lines)
    display_lines: list[int] = []
    all_lines: list[tuple[int, str]] = []
    lines_list = linecache.getlines(filename)
    total_lines = len(lines_list)
    for l in range(display_start, display_end + 1):
        if l <= total_lines:
            line = lines_list[l-1]
            if line.strip():
                display_lines.append(l)
                all_lines.append((l, line.rstrip()))
    
    # Build complete text and apply column-based segmentation
    complete_text_lines = [line_content for line_num, line_content in all_lines]
    complete_text = '\n'.join(complete_text_lines)
    
    # Find absolute positions for cutting within the filtered text
    line_start_positions: list[tuple[int, int]] = [] # record line number and absolute position
    current_pos = 0
    for line_num, line_content in all_lines:
        line_start_positions.append((line_num, current_pos))
        current_pos += len(line_content) + 1  # +1 for newline
    
    # Find start and end absolute positions
    start_abs_pos = None
    end_abs_pos = None
    
    for line_num, line_start_pos in line_start_positions:
        if line_num == start_line:
            start_abs_pos = line_start_pos + col_start
        if line_num == end_line:
            end_abs_pos = line_start_pos + col_end

    # Handle case where positions might not be found
    if start_abs_pos is None:
        start_abs_pos = 0
    if end_abs_pos is None:
        end_abs_pos = len(complete_text)

    source_segment_before = complete_text[:start_abs_pos]
    source_segment = complete_text[start_abs_pos:end_abs_pos]
    source_segment_after = complete_text[end_abs_pos:]
    
    return source_segment_before, source_segment, source_segment_after, display_lines

@functools.lru_cache(maxsize=32)
def _get_code_ast(code: CodeType) -> ast.AST | None:
    try:
        if code.co_name == '<module>':
            lines = linecache.getlines(code.co_filename)
            start_lineno = 1
        else:
            lines, start_lineno = inspect.getsourcelines(code)
        
        # Calculate indentation removed by dedent
        indent_len = 0
        if lines:
            indent_len = len(lines[0]) - len(lines[0].lstrip())
            
        source = "".join(lines)
        dedented_source = textwrap.dedent(source)
        tree = ast.parse(dedented_source)
        
        # Shift line numbers to match absolute file lines
        ast.increment_lineno(tree, start_lineno - 1)
        
        # Shift column offsets to match original file columns
        if indent_len > 0:
            for node in ast.walk(tree):
                if isinstance(node, (ast.expr, ast.stmt, ast.arg, ast.keyword, ast.alias, ast.withitem)):
                     if hasattr(node, 'col_offset'):
                         node.col_offset += indent_len
                     if hasattr(node, 'end_col_offset') and node.end_col_offset is not None:
                         node.end_col_offset += indent_len
        
        return tree
    except Exception:
        return None

def _create_luna_frame(
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
    if start_line is None:
        start_line = frame.f_lineno
    if end_line is None:
        end_line = start_line

    # Split source code into three segments
    source_segment_before, source_segment, source_segment_after, display_lines = _split_source_code(
        filename, start_line, end_line, col_start, col_end
    )

    trace_tree = []
    tree = _get_code_ast(frame.f_code)
        
    if tree:
        target_node = _find_search_node(
            tree,
            start_line,
            end_line,
            col_start,
            col_end
        )
        
        if target_node:
            tracer = ExprTracer(frame, pos=(1, 1, 0, 0))
            result = tracer.visit(target_node)

            if result:
                 if isinstance(result, list):
                     trace_tree = result
                 elif isinstance(result, TraceNode):
                     trace_tree = [result]
                 
                 if len(trace_tree) == 1 and trace_tree[0].children:
                      trace_tree = trace_tree[0].children

    source_segment_pos = (start_line, end_line, col_start, col_end)
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

def collect_frames(exc_traceback):
    tb = exc_traceback
    frame_list = []
    from .config import MAX_TRACE_DEPTH
    while tb:
        frame = tb.tb_frame
        luna_frame = _create_luna_frame(frame, tb.tb_lasti)
        frame_list.append(luna_frame)
        tb = tb.tb_next
    if len(frame_list) > MAX_TRACE_DEPTH:
        skip = len(frame_list) - MAX_TRACE_DEPTH
        frame_list = frame_list[skip:]
    return frame_list