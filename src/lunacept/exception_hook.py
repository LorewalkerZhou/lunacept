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
import sys
import threading
import types

from .instrumentor import run_instrument
from .output import render_exception_output

_INSTALLED = False

def _print_exception(exc_type, exc_value, exc_traceback):
    output_lines = render_exception_output(exc_type, exc_value, exc_traceback)
    print(output_lines, end="")


def _excepthook(exc_type, exc_value, exc_traceback):
    _print_exception(exc_type, exc_value, exc_traceback)


def _threading_excepthook(exc):
    _excepthook(exc.exc_type, exc.exc_value, exc.exc_traceback)


def install():
    """Take over exception printing for main thread and subthreads"""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    
    sys.excepthook = _excepthook
    threading.excepthook = _threading_excepthook

    caller_frame = sys._getframe(1)
    mod = sys.modules[caller_frame.f_globals["__name__"]]
    modules = [mod]

    for mod in modules:
        for name, obj in list(vars(mod).items()):
            if inspect.isfunction(obj):
                setattr(mod, name, run_instrument(obj))


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
