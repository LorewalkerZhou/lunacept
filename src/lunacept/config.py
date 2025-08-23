#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : config.py
@Author  : LorewalkerZhou
@Time    : 2025/8/23 19:57
@Desc    : 
"""
ENABLE_COLORS = True


def configure(*, colors=None):
    """Configure lunacept output style

    Args:
        colors: Whether to enable colored output (default: True)
    """
    global ENABLE_COLORS
    if colors is not None:
        ENABLE_COLORS = colors
