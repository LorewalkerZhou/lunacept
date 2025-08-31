#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : parse.py.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 11:49
@Desc    : 
"""
import ast
import linecache
from dataclasses import dataclass
from types import FrameType
from typing import Any

@dataclass(frozen=True)
class TraceVar:
    name: str
    value: object

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
    trace_vars: list[TraceVar]

class VarExtractor(ast.NodeVisitor):
    def __init__(
            self,
            frame: FrameType,
            pos: tuple[int, int, int, int]
    ):
        self.vars: list[TraceVar] = list()
        self.frame = frame
        self.pos = pos

    def _get_value(self, name: str) -> Any:
        if name in self.frame.f_locals:
            return self.frame.f_locals[name]
        if name in self.frame.f_globals:
            return self.frame.f_globals[name]
        return "<unknow>"

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            value = self._get_value(node.id)
            trace_var = TraceVar(node.id, value)
            self.vars.append(trace_var)

    def visit_Call(self, node: ast.Call):
        expr_str = ast.unparse(node)
        lineno = node.lineno + self.pos[0] - 1
        end_lineno = (node.end_lineno if node.end_lineno else lineno) + self.pos[0] -1
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset
        if node.lineno == 1:
            col_offset += self.pos[2]
            end_col_offset += self.pos[2]
        ori_str = f"{expr_str}-{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"

        import hashlib
        hash_str = hashlib.md5(ori_str.encode()).hexdigest()[0:12]
        name = f"__luna_tmp_{hash_str}"
        value = self._get_value(name)
        trace_var = TraceVar(expr_str, value)
        self.vars.append(trace_var)
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw.value)

    def visit_Attribute(self, node: ast.Attribute):
        self.visit(node.value)

    def visit_Subscript(self, node: ast.Subscript):
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Tuple(self, node: ast.Tuple):
        for elt in node.elts:
            self.visit(elt)

    def visit_List(self, node: ast.List):
        for elt in node.elts:
            self.visit(elt)

    def visit_BinOp(self, node: ast.BinOp):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        self.visit(node.operand)

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
    var_names = extract_vars_from_line(frame, source_segment, source_segment_pos)
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
        trace_vars= var_names
    )

def extract_vars_from_line(
        frame: FrameType,
        source_line: str,
        pos: tuple[int, int, int, int]
) -> list[TraceVar]:
    """Parse source code and return variable names involved in the expression"""
    try:
        tree = ast.parse(source_line, mode='exec')
    except Exception as e:
        return []

    extractor = VarExtractor(frame, pos)
    extractor.visit(tree)
    return extractor.vars
