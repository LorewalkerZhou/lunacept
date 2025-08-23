#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : output.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 13:34
@Desc    : 
"""
import sys

from .config import ENABLE_COLORS
from .parse import LunaFrame

def _get_color_codes():
    """Get color codes (if terminal supports and config enabled)"""
    import os
    if (not ENABLE_COLORS or
            os.getenv('NO_COLOR') or
            not hasattr(sys.stderr, 'isatty') or
            not sys.stderr.isatty()):
        return {
            'red': '', 'yellow': '', 'green': '', 'blue': '', 'magenta': '', 'cyan': '',
            'bold': '', 'dim': '', 'reset': ''
        }
    return {
        'red': '\033[91m', 'yellow': '\033[93m', 'green': '\033[92m',
        'blue': '\033[94m', 'magenta': '\033[95m', 'cyan': '\033[96m',
        'bold': '\033[1m', 'dim': '\033[2m', 'reset': '\033[0m'
    }


def format_variable_value(value, max_length=100):
    """Format variable values, handling large data structures"""
    try:
        # Get repr string
        repr_str = repr(value)

        # If length is appropriate, return directly
        if len(repr_str) <= max_length:
            return repr_str

        # Handle different types of large data structures
        if isinstance(value, (list, tuple)):
            type_name = "list" if isinstance(value, list) else "tuple"
            if len(value) <= 5:
                return repr_str
            else:
                # Show first few elements
                sample = repr(value[:3])[:-1] + f", ... +{len(value) - 3} more]"
                if isinstance(value, tuple):
                    sample = sample.replace('[', '(').replace(']', ')')
                return sample

        elif isinstance(value, dict):
            if len(value) <= 3:
                return repr_str
            else:
                # Show first few key-value pairs
                items = list(value.items())[:2]
                sample_dict = {k: v for k, v in items}
                sample = repr(sample_dict)[:-1] + f", ... +{len(value) - 2} more}}"
                return sample

        elif isinstance(value, str):
            if len(value) <= 50:
                return repr_str
            else:
                return repr(value[:47] + "...")

        else:
            # For other types, truncate repr string
            if len(repr_str) > max_length:
                return repr_str[:max_length - 3] + "..."
            return repr_str

    except Exception:
        # If repr fails, return type information
        return f"<{type(value).__name__} object>"


def _colorize_code(source_line, colors):
    """Perform AST analysis and syntax highlighting on code"""
    import ast
    import keyword
    import re

    try:
        # Try to parse the code line
        tree = ast.parse(source_line.strip())
    except:
        # If parsing fails, return original code
        return source_line

    # Create simple syntax highlighting
    result = source_line

    # Highlight keywords
    for kw in keyword.kwlist:
        pattern = r'\b' + re.escape(kw) + r'\b'
        result = re.sub(pattern, f"{colors['magenta']}{colors['bold']}{kw}{colors['reset']}", result)

    # Highlight strings
    string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
    result = re.sub(string_pattern, f"{colors['green']}\\g<0>{colors['reset']}", result)

    # Highlight numbers
    number_pattern = r'\b\d+\.?\d*\b'
    result = re.sub(number_pattern, f"{colors['cyan']}\\g<0>{colors['reset']}", result)

    # Highlight function calls
    function_pattern = r'(\w+)(\s*\()'
    result = re.sub(function_pattern, f"{colors['blue']}\\1{colors['reset']}\\2", result)

    # Highlight comments
    comment_pattern = r'(#.*)$'
    result = re.sub(comment_pattern, f"{colors['dim']}\\1{colors['reset']}", result)

    return result

def print_exception(exc_type, exc_value, exc_traceback, frame_list: list[LunaFrame]):
    colors = _get_color_codes()
    print(f"{colors['red']}{colors['bold']}" + "=" * 60 + f"{colors['reset']}")
    print(f"{colors['red']}{colors['bold']}   {exc_type.__name__}: {exc_value}{colors['reset']}")
    print(f"{colors['red']}{'=' * 60}{colors['reset']}")
    print()
    frame_count = 0
    for luna_frame in frame_list:
        # Only show variables directly used in the expression
        vars_to_show = list(luna_frame.var_names)

        # Format variable values (handle large data structures)
        local_values = {}
        for var in vars_to_show:
            value = luna_frame.frame.f_locals.get(var, '<undefined>')
            formatted_value = format_variable_value(value)
            local_values[var] = formatted_value

        import os
        short_filename = os.path.basename(luna_frame.filename)
        start_line, end_line, col_start, col_end = luna_frame.source_segment_pos

        # Build position information
        if col_start is not None and col_end is not None:
            if end_line and end_line != start_line:
                location = f"lines {start_line}-{end_line}, cols {col_start}-{col_end}"
            else:
                location = f"line {start_line}, cols {col_start}-{col_end}"
        else:
            if end_line and end_line != start_line:
                location = f"lines {start_line}-{end_line}"
            else:
                location = f"line {start_line}"

        print(f"{colors['dim']}{'─' * 60}{colors['reset']}")
        print()

        frame_count += 1
        print(
            f"{colors['blue']}{colors['bold']}Frame #{frame_count}: {short_filename}:{start_line}{colors['reset']} {colors['dim']}in {luna_frame.func_name}(){colors['reset']}")
        print(f"{colors['cyan']}   {location}{colors['reset']}")
        print()

        box_width = 80  # Fixed frame width
        print(f"   ┌" + "─" * box_width + "┐")

        for line_num, line_content in luna_frame.display_lines:
            is_error_line = start_line <= line_num <= end_line

            # Truncate overly long lines
            max_content_len = box_width - 8  # Reserve space for line number and borders " NNN │ " + " │"
            if len(line_content) > max_content_len:
                line_content = line_content[:max_content_len - 3] + "..."

            colorized_line = _colorize_code(line_content, colors)

            # Calculate padding space: total width - used space
            line_prefix_len = 7  # Length of " NNN │ "
            used_space = line_prefix_len + len(line_content)
            padding = box_width - used_space

            if is_error_line:
                # Error line: red highlighting
                print(
                    f"   │{colors['red']}{colors['bold']} {line_num:>3} │{colors['reset']} {colorized_line}{' ' * padding}│")
            else:
                # Context line: dim display
                print(f"   │{colors['dim']} {line_num:>3} │{colors['reset']} {colorized_line}{' ' * padding}│")

        print(f"   └" + "─" * box_width + "┘")

        if local_values:
            print()
            print(f"{colors['green']}{colors['bold']}Variables:{colors['reset']}")
            for k, v in local_values.items():
                print(
                    f"{colors['green']}   {colors['bold']}{k}{colors['reset']} {colors['dim']}={colors['reset']} {colors['cyan']}{v}{colors['reset']}")

