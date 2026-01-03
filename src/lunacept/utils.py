#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : utils.py
@Author  : LorewalkerZhou
@Time    : 2025/8/31 16:35
@Desc    : Utility functions for project root detection and module path checking
"""
import os
import sys


def get_project_root():
    """Get the project root directory by finding the __main__ module's directory"""
    # Try to get from __main__ module first
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, '__file__') and main_module.__file__:
            main_file = os.path.abspath(main_module.__file__)
            return os.path.dirname(main_file)
    
    # Fallback: use the caller's file directory
    try:
        caller_frame = sys._getframe(1)
        caller_file = caller_frame.f_globals.get('__file__')
        if caller_file:
            return os.path.dirname(os.path.abspath(caller_file))
    except (ValueError, AttributeError):
        pass
    
    return None


def is_module_in_project_by_path(file_path, project_root):
    """Check if a file path is within the project directory."""
    if not file_path or not project_root:
        return False

    try:
        file_path_abs = os.path.abspath(file_path)
        project_root_abs = os.path.abspath(project_root)

        # Ensure project_root_abs ends with separator for proper matching
        if not project_root_abs.endswith(os.sep):
            project_root_abs += os.sep

        if not file_path_abs.startswith(project_root_abs):
            return False

        # Exclude standard library, site-packages, and __pycache__
        if 'site-packages' in file_path_abs or '__pycache__' in file_path_abs:
            return False

        # Exclude .pyc files
        if file_path_abs.endswith('.pyc'):
            return False

        return True
    except (OSError, AttributeError):
        return False


def is_module_in_project(module, project_root):
    """Check if a module is within the project directory"""
    if not hasattr(module, '__file__') or not module.__file__:
        return False
    module_path = os.path.abspath(module.__file__)

    return is_module_in_project_by_path(module_path, project_root)

