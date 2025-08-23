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
    display_lines: list[tuple[int, str]]
    source_segment: str
    source_segment_pos: tuple[int, int, int, int]  # start_line, end_line, col_start, col_end
    var_names: set[str]


def normalize_expr_safe(src: str) -> str:
    out_tokens = []
    f = io.StringIO(src).readline
    for tok in tokenize.generate_tokens(f):
        tok_type, tok_str, *_ = tok
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
    display_lines = []
    for l in range(display_start, display_end + 1):
        line = linecache.getline(filename, l)
        if line.strip():  # Only add non-empty lines
            display_lines.append((l, line.rstrip()))

    source_lines = [linecache.getline(filename, l) for l in range(start_line, end_line + 1)]

    # Extract precise code segment from (start_line, col_start) to (end_line, col_end) for parsing
    source_segment = "".join(source_lines).rstrip()  # Default to using complete code
    if col_start is not None and col_end is not None:
        if start_line == end_line:
            line_content = source_lines[0].rstrip()
            if col_start < len(line_content):
                if col_end <= len(line_content):
                    source_segment = line_content[col_start:col_end]
                else:
                    source_segment = line_content[col_start:]
            else:
                source_segment = ""
        else:
            result_lines = []
            for i, line in enumerate(source_lines):
                line_content = line.rstrip()
                if i == 0:  # First line: start from col_start
                    if col_start < len(line_content):
                        result_lines.append(line_content[col_start:])
                elif i == len(source_lines) - 1:  # Last line: end at col_end
                    if col_end <= len(line_content):
                        result_lines.append(line_content[:col_end])
                    else:
                        result_lines.append(line_content)
                else:  # Middle lines: keep complete
                    result_lines.append(line_content)
            source_segment = "\n".join(result_lines).rstrip()
            source_segment = normalize_expr_safe(source_segment)

    var_names = extract_vars_from_line(source_segment)

    return LunaFrame(
        frame=frame,
        filename = frame.f_code.co_filename,
        func_name = frame.f_code.co_name,
        tb_lasti = tb_lasti,
        display_lines = display_lines,
        source_segment = source_segment,
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







