#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for lunacept.

Usage:
    python -m lunacept script.py arg1 arg2 ...
    lunacept script.py [args...]
"""
import sys
import os
import ast
import tokenize
import types

from .instrumentor import Instrumentor
from .exception_hook import install


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m lunacept script.py [args...]")
        print("       lunacept script.py [args...]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    
    if not os.path.exists(script_path):
        print(f"Error: Script '{script_path}' not found")
        sys.exit(1)
    
    script_path = os.path.abspath(script_path)
    
    install()
    
    original_argv = sys.argv[:]
    sys.argv = [script_path] + sys.argv[2:]
    
    project_root = os.path.dirname(script_path)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        with tokenize.open(script_path) as f:
            source = f.read()

        try:
            tree = ast.parse(source, filename=script_path)
        except SyntaxError:
            raise

        instrumentor = Instrumentor(first_line=1, indent_offset=0)
        new_tree = instrumentor.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        code = compile(new_tree, filename=script_path, mode="exec")

        main_globals = {
            '__name__': '__main__',
            '__file__': script_path,
            '__doc__': None,
            '__builtins__': __builtins__,
        }
        
        old_main = sys.modules.get('__main__')
        
        main_module = types.ModuleType('__main__')
        main_module.__dict__.update(main_globals)
        sys.modules['__main__'] = main_module

        exec(code, main_module.__dict__)
        
    except SystemExit as e:
        sys.exit(e.code if e.code is not None else 0)
    finally:
        sys.argv = original_argv


if __name__ == '__main__':
    main()

