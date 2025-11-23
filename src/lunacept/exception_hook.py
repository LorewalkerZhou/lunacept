#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : exception_hook.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:22
@Desc    : 
"""
import functools
import inspect
import os
import sys
import threading
import types

from .instrumentor import run_instrument
from .output import render_exception_output

_INSTALLED = False
_INSTRUMENTED_MODULES = set()

def _print_exception(exc_type, exc_value, exc_traceback):
    output_lines = render_exception_output(exc_type, exc_value, exc_traceback)
    print(output_lines, end="")


def _excepthook(exc_type, exc_value, exc_traceback):
    _print_exception(exc_type, exc_value, exc_traceback)


def _threading_excepthook(exc):
    _excepthook(exc.exc_type, exc.exc_value, exc.exc_traceback)


def _get_project_root():
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

def _is_module_in_project(module, project_root):
    """Check if a module is within the project directory"""
    if not hasattr(module, '__file__') or not module.__file__:
        return False
    
    try:
        module_path = os.path.abspath(module.__file__)
        project_root_abs = os.path.abspath(project_root)
        
        if not module_path.startswith(project_root_abs):
            return False
        
        # Exclude standard library, site-packages, and __pycache__
        if 'site-packages' in module_path or '__pycache__' in module_path:
            return False
        
        # Exclude .pyc files
        if module_path.endswith('.pyc'):
            return False
        
        return True
    except (OSError, AttributeError):
        return False

def _instrument_module(mod):
    """Instrument all functions in a module"""
    if mod in _INSTRUMENTED_MODULES:
        return
    
    _INSTRUMENTED_MODULES.add(mod)
    
    for name, obj in list(vars(mod).items()):
        if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
            try:
                setattr(mod, name, run_instrument(obj))
            except Exception as e:
                # Silently skip functions that can't be instrumented
                pass

def install():
    """Take over exception printing for main thread and subthreads"""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    
    sys.excepthook = _excepthook
    threading.excepthook = _threading_excepthook

    project_root = _get_project_root()
    if not project_root:
        # Fallback to current module only
        try:
            caller_frame = sys._getframe(1)
            mod = sys.modules[caller_frame.f_globals["__name__"]]
            _instrument_module(mod)
        except (ValueError, KeyError):
            pass
        return

    # Instrument all loaded modules in the project
    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        
        if _is_module_in_project(mod, project_root):
            _instrument_module(mod)


def capture_exceptions(func: types.FunctionType, reraise=False):
    """
    Decorator to automatically capture  and display exceptions.
    """
    try:
        instruct_func = run_instrument(func)
    except Exception as e:
        print(f"[lunacept] Failed to instrument {func.__name__}: {e}")
        instruct_func = func

    @functools.wraps(instruct_func)
    def wrapper(*args, **kwargs):
        try:
            return instruct_func(*args, **kwargs)
        except Exception as exc:
            exc_type = type(exc)
            exc_value = exc
            exc_traceback = exc.__traceback__
            _print_exception(exc_type, exc_value, exc_traceback)
            if reraise:
                raise
            return None

    return wrapper


def render_exception(exc: BaseException, enable_color=False) -> str:
    """
    Render an already captured exception into Luna-formatted string output.
    """
    exc_type = type(exc)
    exc_traceback = exc.__traceback__
    return render_exception_output(exc_type, exc, exc_traceback, enable_color=enable_color)

def print_exception(exc: BaseException):
    """
    Print an already captured exception into Luna-formatted string output.
    """
    exc_type = type(exc)
    exc_traceback = exc.__traceback__
    _print_exception(exc_type, exc, exc_traceback)
