#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : __init__.py.py
@Author  : LorewalkerZhou
@Time    : 2025/8/16 20:21
@Desc    : 
"""
from .exception_hook import install
from .config import configure

__all__ = ["install", "configure"]