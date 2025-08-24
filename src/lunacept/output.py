#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : output.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 13:34
@Desc    : 
"""
import io
import keyword
import sys
import token
import tokenize

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


def format_variable_value(value, max_length: int = 100, _depth: int = 0, _max_depth: int = 2) -> str:
    """Format variable values, handling basic and large data structures."""
    try:
        if isinstance(value, (int, float, bool, type(None), str, complex, bytes, bytearray, frozenset, set, list, tuple,
                              dict)):
            repr_str = repr(value)
            if len(repr_str) > max_length:
                return repr_str[:max_length - 3] + "..."
            return repr_str

        cls = type(value)
        #
        if cls.__repr__ is not object.__repr__:
            repr_str = repr(value)
            if len(repr_str) > max_length:
                return repr_str[:max_length - 3] + "..."
            return repr_str

        if _depth >= _max_depth:
            return f"<{cls.__name__} object>"

        members = getattr(value, "__dict__", {})
        parts = []
        for k, v in members.items():
            parts.append(f"{k}={format_variable_value(v, max_length, _depth=_depth + 1, _max_depth=_max_depth)}")
        return f"{cls.__name__}({', '.join(parts)})"

    except Exception:
        return f"<{type(value).__name__} object>"


def _colorize_code(source_code, colors):
    """Perform AST analysis and syntax highlighting on code"""
    # Split source into lines and colorize each line separately to avoid cross-line issues
    lines = source_code.split('\n')
    colorized_lines = []
    
    for line in lines:
        if not line.strip():
            # Empty or whitespace-only lines
            colorized_lines.append(line)
            continue
            
        try:
            result = ""
            readline = io.BytesIO(line.encode("utf-8")).readline
            last_end = 0  # column position in current line
            
            for tok in tokenize.tokenize(readline):
                tok_type = tok.type
                tok_str = tok.string
                start_col = tok.start[1]
                end_col = tok.end[1]

                if tok_type in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL):
                    continue

                # Add spaces between tokens
                if start_col > last_end:
                    result += " " * (start_col - last_end)

                # Apply colors based on token type
                if tok_type == token.STRING:
                    result += f"{colors['green']}{tok_str}{colors['reset']}"
                elif tok_type == token.NUMBER:
                    result += f"{colors['cyan']}{tok_str}{colors['reset']}"
                elif tok_type == token.COMMENT:
                    result += f"{colors['dim']}{tok_str}{colors['reset']}"
                elif tok_type == token.NAME:
                    if tok_str in keyword.kwlist:
                        result += f"{colors['magenta']}{colors['bold']}{tok_str}{colors['reset']}"
                    else:
                        result += f"{colors['blue']}{tok_str}{colors['reset']}"
                elif tok_type == token.OP:
                    result += f"{colors['yellow']}{tok_str}{colors['reset']}"
                else:
                    result += tok_str

                last_end = end_col

            colorized_lines.append(result)
            
        except tokenize.TokenError:
            # If tokenization fails, use original line
            colorized_lines.append(line)
    
    return '\n'.join(colorized_lines)

def print_exception(exc_type, exc_value, exc_traceback, frame_list: list[LunaFrame]):
    colors = _get_color_codes()
    frame_count = 0
    for luna_frame in frame_list:
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

        if luna_frame.source_segment_before:
            colored_before = "\n".join(
                f"{colors['dim']}{line}{colors['reset']}"
                for line in luna_frame.source_segment_before.splitlines()
            )
        else:
            colored_before = ""
        colored_segment = _colorize_code(luna_frame.source_segment, colors) if luna_frame.source_segment else ""
        if luna_frame.source_segment_after:
            colored_after = "\n".join(
                f"{colors['dim']}{line}{colors['reset']}"
                for line in luna_frame.source_segment_after.splitlines()
            )
        else:
            colored_after = ""
        
        combined_text = colored_before + colored_segment + colored_after
        combined_lines = combined_text.split('\n')

        assert len(combined_lines) == len(luna_frame.display_lines)
        for i, line_num in enumerate(luna_frame.display_lines):
            line_content = combined_lines[i]
            print(f"{line_num:>3} │ {line_content}")

        vars_to_show = list(luna_frame.var_names)

        local_values = {}
        for var in vars_to_show:
            if var in luna_frame.frame.f_locals:
                value = luna_frame.frame.f_locals[var]
            elif var in luna_frame.frame.f_globals:

                value = luna_frame.frame.f_globals[var]
            else:
                value = "<undefined>"
            # Format variable values (handle large data structures)
            formatted_value = format_variable_value(value)
            local_values[var] = formatted_value


        if local_values:
            print()
            print(f"{colors['green']}{colors['bold']}Variables:{colors['reset']}")
            for k, v in local_values.items():
                print(
                    f"{colors['green']}   {colors['bold']}{k}{colors['reset']} {colors['dim']}={colors['reset']} {colors['cyan']}{v}{colors['reset']}")

    print(f"{colors['red']}{colors['bold']}" + "=" * 60 + f"{colors['reset']}")
    print(f"{colors['red']}{colors['bold']}   {exc_type.__name__}: {exc_value}{colors['reset']}")
    print(f"{colors['red']}{'=' * 60}{colors['reset']}")
    print()

