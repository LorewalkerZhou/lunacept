#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : parse.py.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 11:49
@Desc    : 
"""
import ast
import io
import linecache
import tokenize
from dataclasses import dataclass
from types import FrameType


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
    var_names: set[str]


def normalize_expr_safe(src: str) -> str:
    out_tokens = []
    f = io.BytesIO(src.encode("utf-8")).readline
    for tok in tokenize.tokenize(f):
        tok_type, tok_str, *_ = tok
        if tok_type in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if tok_type == tokenize.NL or tok_type == tokenize.NEWLINE:
            out_tokens.append(" ")
        else:
            out_tokens.append(tok_str)
    return "".join(out_tokens).strip()

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
    
    # Use normalized version only for variable extraction
    normalized_segment = normalize_expr_safe(source_segment)
    var_names = extract_vars_from_line(normalized_segment)
    return LunaFrame(
        frame=frame,
        filename = frame.f_code.co_filename,
        func_name = frame.f_code.co_name,
        tb_lasti = tb_lasti,
        display_lines = display_lines,
        source_segment = source_segment,
        source_segment_before = source_segment_before,
        source_segment_after = source_segment_after,
        source_segment_pos = (start_line, end_line, col_start, col_end),
        var_names = var_names
    )

def extract_vars_from_line(source_line: str) -> set[str]:
    """Parse source code and return variable names involved in the expression"""
    try:
        # Remove leading whitespace
        import textwrap
        cleaned_source = textwrap.dedent(source_line).strip()
        tree = ast.parse(cleaned_source)
    except Exception:
        return set()

    # Collect assignment targets (left-value variables) and comprehension loop variables
    assign_targets = set()
    comprehension_vars = set()

    # For multi-statements, we need smarter handling
    # Simplified strategy: if multi-statement with semicolons, prioritize variables from the last statement
    if ';' in cleaned_source:
        # Multi-statement case, analyze the last statement
        statements = cleaned_source.split(';')
        last_statement = statements[-1].strip()
        if last_statement:
            try:
                last_tree = ast.parse(last_statement)
                # Only consider assignment targets from the last statement
                for node in ast.walk(last_tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                assign_targets.add(target.id)
                            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                                for elt in target.elts:
                                    if isinstance(elt, ast.Name):
                                        assign_targets.add(elt.id)
            except:
                pass  # If parsing fails, fallback to global analysis

    if not assign_targets or ';' not in cleaned_source:
        # Handle single statement or failed multi-statement parsing
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assign_targets.add(target.id)
                    elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                assign_targets.add(elt.id)

    # Collect loop variables from comprehensions, lambda parameters, and for loops
    for node in ast.walk(tree):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for generator in node.generators:
                if isinstance(generator.target, ast.Name):
                    comprehension_vars.add(generator.target.id)
                elif isinstance(generator.target, (ast.Tuple, ast.List)):
                    for elt in generator.target.elts:
                        if isinstance(elt, ast.Name):
                            comprehension_vars.add(elt.id)

        elif isinstance(node, ast.Lambda):
            for arg in node.args.args:
                comprehension_vars.add(arg.arg)

        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                comprehension_vars.add(node.target.id)
            elif isinstance(node.target, (ast.Tuple, ast.List)):
                for elt in node.target.elts:
                    if isinstance(elt, ast.Name):
                        comprehension_vars.add(elt.id)

    # Collect right-value variables, but handle function calls more precisely
    vars_in_expr = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            # Skip assignment targets
            if node.id in assign_targets:
                continue
            # Skip comprehension loop variables
            if node.id in comprehension_vars:
                continue
            # Skip built-in functions and keywords
            if node.id in {'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple'}:
                continue
            vars_in_expr.add(node.id)

    # Remove function names from function calls, but keep arguments
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Regular function call: func(args)
                vars_in_expr.discard(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Method call: obj.method(args) - keep obj, remove method
                # method name is not in vars_in_expr since it's attribute access, no special handling needed
                pass

    return vars_in_expr







