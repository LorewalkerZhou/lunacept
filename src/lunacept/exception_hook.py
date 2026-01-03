#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : exception_hook.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:22
@Desc    : 
"""
import functools
import logging
import os
import sys
import threading
import types
from typing import Any, Union

from .instrumentor import (
    InstrumentingFinder,
    run_instrument,
)
from .output import render_exception_output
from .utils import get_project_root

_INSTALLED = False

def _print_exception(exc_type, exc_value, exc_traceback):
    output_lines = render_exception_output(exc_type, exc_value, exc_traceback)
    print(output_lines, end="")


def _excepthook(exc_type, exc_value, exc_traceback):
    _print_exception(exc_type, exc_value, exc_traceback)


def _threading_excepthook(exc):
    _excepthook(exc.exc_type, exc.exc_value, exc.exc_traceback)


def install():
    """Install import hook for automatic instrumentation during module import"""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    def _instrument_threading_run():
        if getattr(threading.Thread, "__luna_patched__", False):
            return

        try:
            original_run = threading.Thread.run
            instrumented_run = run_instrument(original_run)
            threading.Thread.run = instrumented_run
            threading.Thread.__luna_patched__ = True
        except Exception as e:
            pass
    
    sys.excepthook = _excepthook
    threading.excepthook = _threading_excepthook

    _instrument_threading_run()

    project_root = get_project_root()
    if project_root:
        finder = InstrumentingFinder(project_root)
        sys.meta_path.insert(0, finder)

def _create_exception_wrapper(func, reraise=False):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            exc_type = type(exc)
            exc_value = exc
            exc_traceback = exc.__traceback__
            _print_exception(exc_type, exc_value, exc_traceback)
            if reraise:
                raise
            return None
    return wrapper

def capture_exceptions(obj: Union[types.FunctionType, type], reraise=False):
    """
    Decorator to automatically capture  and display exceptions.
    """
    try:
        instruct_obj = run_instrument(obj)
    except Exception as e:
        logging.error(f"[lunacept] Failed to instrument {obj.__name__}: {e}")
        instruct_obj = obj

    if isinstance(instruct_obj, type):
        new_cls = instruct_obj
        for name, attr in list(new_cls.__dict__.items()):
            if isinstance(attr, types.FunctionType):
                setattr(new_cls, name, _create_exception_wrapper(attr, reraise))
        return new_cls
    else:
        return _create_exception_wrapper(instruct_obj, reraise)



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
