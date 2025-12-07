#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : output.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 13:34
@Desc    : 
"""
from io import StringIO
from typing import Any

from rich.console import Console, Group
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.syntax import Syntax
from rich.tree import Tree

from .config import ENABLE_COLORS
from .parse import TraceNode, collect_frames


def _format_variable_value(value: Any, _depth: int = 0) -> str:
    """Format variable values, handling basic and large data structures."""
    from .config import MAX_VALUE_LENGTH, MAX_VALUE_DEPTH
    try:
        if isinstance(value, (int, float, bool, type(None), str, complex, bytes, bytearray, frozenset, set, list, tuple,
                              dict)):
            repr_str = repr(value)
            if len(repr_str) > MAX_VALUE_LENGTH:
                return repr_str[:MAX_VALUE_LENGTH - 3] + "..."
            return repr_str

        cls = type(value)

        if cls.__repr__ is object.__repr__:
            if _depth >= MAX_VALUE_DEPTH:
                return f"<{cls.__name__} object>"

            members = getattr(value, "__dict__", {})
            parts = []
            for k, v in members.items():
                parts.append(f"{k}={_format_variable_value(v, _depth=_depth + 1)}")
            return f"{cls.__name__}({', '.join(parts)})"
        else:
            repr_str = repr(value)
            if len(repr_str) > MAX_VALUE_LENGTH:
                return repr_str[:MAX_VALUE_LENGTH - 3] + "..."
            return repr_str

    except Exception:
        return f"<{type(value).__name__} object>"


def _build_rich_tree(nodes: list[TraceNode], normalized_segment: str) -> Tree:
    """Build a Rich Tree from TraceNode list."""
    root = Tree("Expr Tree:", style="bold green")
    
    def add_node(tree: Tree, node: TraceNode):
        """Recursively add nodes to the tree."""
        # Build the label for this node
        label_parts = []
        
        # Add expression name if it's different from the normalized segment
        if node.expr:
            if not normalized_segment or ''.join(node.expr.split()) != normalized_segment:
                label_parts.append(("bold", node.expr))
                label_parts.append(("dim", " = "))
        
        # Add formatted value
        formatted_value = _format_variable_value(node.value)
        label_parts.append(("cyan", formatted_value))
        
        # Create the label Text
        label = Text()
        for style, text in label_parts:
            label.append(text, style=style)
        
        # Create child tree node
        child_tree = tree.add(label)
        # Add children recursively
        for child in node.children:
            if child:
                add_node(child_tree, child)
    
    # Add all root nodes
    for node in nodes:
        add_node(root, node)
    
    return root

def render_exception_output(exc_type, exc_value, exc_traceback, enable_color=True) -> str:
    """Render exception output using Rich for better formatting."""
    no_color = not (ENABLE_COLORS and enable_color)
    import os
    if not no_color:
        os.environ['FORCE_COLOR'] = '1'
        os.environ['TERM'] = 'xterm-256color'
    console = Console(file=StringIO(), force_terminal=not no_color, no_color=no_color, legacy_windows=False)
    
    frame_list = collect_frames(exc_traceback)
    
    console.print("[bold red]Traceback (most recent call last)[/bold red]")

    for frame_count, luna_frame in enumerate(frame_list, 1):
        start_line, end_line, col_start, col_end = luna_frame.source_segment_pos

        # Build position information
        location_desc = ""
        if col_start is not None and col_end is not None:
            if end_line and end_line != start_line:
                location_desc = f"lines {start_line}-{end_line}, cols {col_start}-{col_end}"
            else:
                location_desc = f"line {start_line}, cols {col_start}-{col_end}"
        else:
            if end_line and end_line != start_line:
                location_desc = f"lines {start_line}-{end_line}"
            else:
                location_desc = f"line {start_line}"

        # Build header text
        header = f"[blue]Frame #{frame_count}[/blue]: [link=file://{luna_frame.filename}]{luna_frame.filename}:{start_line}[/link] in [bold]{luna_frame.func_name}[/bold]"
        
        # Build Content Group
        content_renderables = []
        
        # 1. Location details
        content_renderables.append(Text(f"Location: {location_desc}", style="cyan"))
        content_renderables.append(Text("")) #

        # 2. Source Code Construction
        import linecache
        source_code_group = []
        
        # We don't need the split segments anymore for display, just for logic if needed.
        # But we still use luna_frame.display_lines
        
        for line_num in luna_frame.display_lines:
            line_text = Text()
            
            # Line Number
            if start_line <= line_num <= end_line:
                 line_text.append(f"{line_num:>4} │ ", style="bold")
            else:
                 line_text.append(f"{line_num:>4} │ ", style="dim")

            # Source Code
            code_line = linecache.getline(luna_frame.filename, line_num).rstrip('\n')
            if not code_line:
                # Handle empty lines or EOF
                source_code_group.append(line_text)
                continue

            # Full Syntax Highlighting
            if not no_color:
                syntax = Syntax(
                    code_line, 
                    "python", 
                    theme="monokai", 
                    line_numbers=False, 
                    code_width=len(code_line),
                    background_color="default"
                )
                # Convert Syntax to Text
                code_text = Text()
                for segment in console.render(syntax):
                    if segment.text != '\n':
                        code_text.append(segment.text, style=segment.style)
            else:
                code_text = Text(code_line)

            # Apply Spotlighting (Dim everything except the error segment)
            if start_line <= line_num <= end_line:
                # Determine range within this line
                hl_start = 0
                hl_end = len(code_line)
                
                if line_num == start_line:
                    hl_start = col_start if col_start is not None else 0
                if line_num == end_line:
                    hl_end = col_end if col_end is not None else len(code_line)
                
                # Dim the parts BEFORE the error segment
                if hl_start > 0:
                    code_text.stylize("dim", start=0, end=hl_start)
                
                # Dim the parts AFTER the error segment
                if hl_end < len(code_line):
                    code_text.stylize("dim", start=hl_end, end=len(code_line))
            
            # Dim non-active lines completely
            if not (start_line <= line_num <= end_line):
                code_text.stylize("dim")

            line_text.append(code_text)
            source_code_group.append(line_text)

        content_renderables.append(Group(*source_code_group))

        tree_nodes = luna_frame.trace_tree
        if tree_nodes:
            content_renderables.append(Padding(Rule(style="dim"), (1, 0))) # Separator
            normalized_segment = ''.join((luna_frame.source_segment or '').split())
            rich_tree = _build_rich_tree(tree_nodes, normalized_segment)
            content_renderables.append(rich_tree)

        panel = Panel(
            Group(*content_renderables),
            title=header,
            border_style="blue",
            padding=(0, 1),
            expand=False
        )
        console.print(panel)

    # Exception type and message
    console.print(f"[bold red]{exc_type.__name__}:[/bold red] {exc_value}")

    output = console.file.getvalue()
    return output
