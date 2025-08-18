#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : core.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:22
@Desc    : 
"""
import ast
import linecache
import sys
import threading

def extract_vars_from_line(source_line):
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
                sample = repr(value[:3])[:-1] + f", ... +{len(value)-3} more]"
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
                sample = repr(sample_dict)[:-1] + f", ... +{len(value)-2} more}}"
                return sample
        
        elif isinstance(value, str):
            if len(value) <= 50:
                return repr_str
            else:
                return repr(value[:47] + "...")
        
        else:
            # For other types, truncate repr string
            if len(repr_str) > max_length:
                return repr_str[:max_length-3] + "..."
            return repr_str
            
    except Exception:
        # If repr fails, return type information
        return f"<{type(value).__name__} object>"


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

def _excepthook(exc_type, exc_value, exc_traceback):
    colors = _get_color_codes()
    
    # Beautified exception title
    print()
    print(f"{colors['red']}{colors['bold']}" + "=" * 60 + f"{colors['reset']}")
    print(f"{colors['red']}{colors['bold']}   {exc_type.__name__}: {exc_value}{colors['reset']}")
    print(f"{colors['red']}{'=' * 60}{colors['reset']}")
    print()

    tb = exc_traceback
    frame_count = 0
    while tb:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        func_name = frame.f_code.co_name

        # Use co_positions to get precise position information
        pos_iter = frame.f_code.co_positions()
        
        # Find position information for the corresponding instruction
        positions = None
        for i, pos in enumerate(pos_iter):
            if i == tb.tb_lasti // 2:  # tb_lasti is bytecode offset, divide by 2 to get instruction index
                positions = pos
                break
        
        if positions and positions[0] is not None:
            start_line, end_line, col_start, col_end = positions
            # If no end line number, default to start line number
            if end_line is None:
                end_line = start_line
                
            # Get all involved lines, including one line of context before and after
            context_start = max(1, start_line - 1)  # Previous line
            context_end = end_line + 1  # Next line
            context_lines = []
            for l in range(context_start, context_end + 1):
                line = linecache.getline(filename, l)
                if line.strip():  # Only add non-empty lines
                    context_lines.append((l, line.rstrip()))
            
            # Complete source code for display
            source_lines = [linecache.getline(filename, l) for l in range(start_line, end_line + 1)]
            source_stmt = "".join(source_lines).rstrip()
            
            # Extract precise code segment from (start_line, col_start) to (end_line, col_end) for parsing
            precise_code_for_parsing = source_stmt  # Default to using complete code
            if col_start is not None and col_end is not None:
                if start_line == end_line:
                    # Single line case: extract code within column range
                    line_content = source_lines[0].rstrip()
                    if col_start < len(line_content):
                        if col_end <= len(line_content):
                            precise_code_for_parsing = line_content[col_start:col_end]
                        else:
                            precise_code_for_parsing = line_content[col_start:]
                    else:
                        precise_code_for_parsing = ""
                else:
                    # Multi-line case: from col_start of first line to col_end of last line
                    result_lines = []
                    for i, line in enumerate(source_lines):
                        line_content = line.rstrip()
                        if i == 0:  # First line: start from col_start
                            if col_start < len(line_content):
                                result_lines.append(line_content[col_start:])
                            # If col_start exceeds line length, skip this line
                        elif i == len(source_lines) - 1:  # Last line: end at col_end
                            if col_end <= len(line_content):
                                result_lines.append(line_content[:col_end])
                            else:
                                result_lines.append(line_content)
                        else:  # Middle lines: keep complete
                            result_lines.append(line_content)
                    precise_code_for_parsing = "\n".join(result_lines).rstrip()
        else:
            # If no position information, use traditional method
            lineno = tb.tb_lineno
            start_line = lineno
            end_line = lineno
            col_start = col_end = None
            
            # Get context lines
            context_start = max(1, lineno - 1)
            context_end = lineno + 1
            context_lines = []
            for l in range(context_start, context_end + 1):
                line = linecache.getline(filename, l)
                if line.strip():  # Only add non-empty lines
                    context_lines.append((l, line.rstrip()))
            
            source_lines = [linecache.getline(filename, lineno)]
            source_stmt = source_lines[0].rstrip()
            precise_code_for_parsing = source_stmt  # When no precise position, use same code for parsing and display
        
        # Use precise code segment for variable extraction, but display complete source code
        var_names = extract_vars_from_line(precise_code_for_parsing)
        
        # Only show variables directly used in the expression
        vars_to_show = list(var_names)
        
        # Format variable values (handle large data structures)
        local_values = {}
        for var in vars_to_show:
            value = frame.f_locals.get(var, '<undefined>')
            formatted_value = format_variable_value(value)
            # Avoid double quoting - if format_variable_value already returns string representation, use directly
            local_values[var] = formatted_value

        # Beautified frame information display
        import os
        short_filename = os.path.basename(filename)
        
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
        
        # Print beautified frame information
        frame_count += 1
        print(f"{colors['blue']}{colors['bold']}Frame #{frame_count}: {short_filename}:{start_line}{colors['reset']} {colors['dim']}in {func_name}(){colors['reset']}")
        print(f"{colors['cyan']}   {location}{colors['reset']}")
        print()
        
        # Source code display (black/white/grey frame, colored content)
        box_width = 80  # Fixed frame width
        print(f"   ┌" + "─" * box_width + "┐")
        
        for line_num, line_content in context_lines:
            is_error_line = start_line <= line_num <= end_line
            
            # Truncate overly long lines
            max_content_len = box_width - 8  # Reserve space for line number and borders " NNN │ " + " │"
            if len(line_content) > max_content_len:
                line_content = line_content[:max_content_len-3] + "..."
            
            colorized_line = _colorize_code(line_content, colors)
            
            # # Remove ANSI color codes to calculate actual display length
            # import re
            # clean_line = re.sub(r'\x1b\[[0-9;]*m', '', colorized_line)
            
            # Calculate padding space: total width - used space
            line_prefix_len = 7  # Length of " NNN │ "
            used_space = line_prefix_len + len(line_content)
            padding = box_width - used_space
            
            if is_error_line:
                # Error line: red highlighting
                print(f"   │{colors['red']}{colors['bold']} {line_num:>3} │{colors['reset']} {colorized_line}{' ' * padding}│")
            else:
                # Context line: dim display  
                print(f"   │{colors['dim']} {line_num:>3} │{colors['reset']} {colorized_line}{' ' * padding}│")
        
        print(f"   └" + "─" * box_width + "┘")
        
        # Beautified variable display
        if local_values:
            print()
            print(f"{colors['green']}{colors['bold']}Variables:{colors['reset']}")
            for k, v in local_values.items():
                print(f"{colors['green']}   {colors['bold']}{k}{colors['reset']} {colors['dim']}={colors['reset']} {colors['cyan']}{v}{colors['reset']}")
        
        # Simple separator line between frames (black/white/grey)
        tb = tb.tb_next
        if tb:  # If there's another frame, add separator line
            print()
            print(f"{colors['dim']}{'─' * 60}{colors['reset']}")
            print()


def _threading_excepthook(exc):
    _excepthook(exc.exc_type, exc.exc_value, exc.exc_traceback)


# Configuration options
ENABLE_COLORS = True

def configure(*, colors=None):
    """Configure lunacept output style
    
    Args:
        colors: Whether to enable colored output (default: True)
    """
    global ENABLE_COLORS
    if colors is not None:
        ENABLE_COLORS = colors

def install():
    """Take over exception printing for main thread and subthreads"""
    sys.excepthook = _excepthook
    if hasattr(threading, "excepthook"):  # Python 3.8+
        threading.excepthook = _threading_excepthook
