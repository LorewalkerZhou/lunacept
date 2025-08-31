#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : exception_hook.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:22
@Desc    : 
"""
import inspect
import sys
import threading

from .instrumentor import run_instrument
from .parse import create_luna_frame
from .output import print_exception

def _excepthook(exc_type, exc_value, exc_traceback):
    tb = exc_traceback
    frame_list = []
    while tb:
        frame = tb.tb_frame
        luna_frame = create_luna_frame(frame, tb.tb_lasti)
        frame_list.append(luna_frame)
        tb = tb.tb_next

    print_exception(exc_type, exc_value, exc_traceback, frame_list)


def _threading_excepthook(exc):
    _excepthook(exc.exc_type, exc.exc_value, exc.exc_traceback)


def install():
    """Take over exception printing for main thread and subthreads"""
    sys.excepthook = _excepthook
    threading.excepthook = _threading_excepthook

    caller_frame = sys._getframe(1)
    mod = sys.modules[caller_frame.f_globals["__name__"]]
    modules = [mod]

    for mod in modules:
        for name, obj in list(vars(mod).items()):
            if inspect.isfunction(obj):
                setattr(mod, name, run_instrument(obj))
