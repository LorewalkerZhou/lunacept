#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : exception_hook.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:22
@Desc    : 
"""
import sys
import threading
import types

from .instrumentor import InstrumentingFinder
from .output import render_exception_output
from . import config

_INSTALLED = False

def _print_exception(exc_type, exc_value, exc_traceback):
    output_lines = render_exception_output(exc_type, exc_value, exc_traceback)
    print(output_lines, end="")


def _excepthook(exc_type, exc_value, exc_traceback):
    _print_exception(exc_type, exc_value, exc_traceback)


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
            from .instrumentor import run_instrument
            original_run = threading.Thread.run
            instrumented_run = (
                run_instrument(original_run))
            threading.Thread.run = instrumented_run
            threading.Thread.__luna_patched__ = True
        except Exception:
            pass
    
    sys.excepthook = _excepthook
    threading.excepthook = _excepthook

    if config.GLOBAL_INSTALL:
        _instrument_threading_run()

    finder = InstrumentingFinder()
    sys.meta_path.insert(0, finder)

def luna_capture(
    obj: types.FunctionType | types.MethodType | types.CoroutineType
):
    """
    Marker function and will be deleted during import.
    """
    raise ValueError("luna_capture should never be called.")


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
