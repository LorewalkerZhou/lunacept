#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : instrumentor.py
@Author  : LorewalkerZhou
@Time    : 2025/8/31 16:35
@Desc    : 
"""
import ast
import importlib
import inspect
import os
import types
import textwrap
import hashlib
import sys
from collections.abc import Sequence
from importlib.abc import MetaPathFinder, Loader
from pathlib import Path
from typing import Union
from importlib.machinery import ModuleSpec



class Instrumentor(ast.NodeTransformer):
    def __init__(
        self,
        tree: ast.Module,
        first_line: int = 1,
        indent_offset: int = 0,
    ):
        super().__init__()
        self.first_line = first_line
        self.indent_offset = indent_offset
        self.tree = tree

    def run(self) -> ast.Module:
        new_tree = self.visit(self.tree)
        ast.fix_missing_locations(new_tree)
        # The AST generated from `ast.parse(source)` always starts line numbering at 1,
        # because the parsed source string is treated as a standalone code snippet.
        # However, when the original function is defined in a file, its first line in
        # that file may be at a higher line number (e.g. line 42). This mismatch would
        # cause traceback and error messages to show incorrect line numbers.
        #
        # `func.__code__.co_firstlineno` gives the actual line number in the source file
        # where the function definition starts. By applying `ast.increment_lineno` with
        # an offset of `(first_line - 1)`, we shift all line numbers in the transformed
        # AST so they align correctly with the original file.
        ast.increment_lineno(new_tree, self.first_line - 1)
        return new_tree

    def _make_temp_var(self, node: ast.expr):
        lineno = node.lineno
        end_lineno = node.end_lineno if node.end_lineno else lineno
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset

        # Adjust column offsets by adding the indentation offset
        if col_offset is not None:
            col_offset += self.indent_offset
        if end_col_offset is not None:
            end_col_offset += self.indent_offset

        lineno += self.first_line - 1
        end_lineno += self.first_line - 1

        ori_str = f"{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"
        hash_str = hashlib.md5(ori_str.encode()).hexdigest()[0:12]
        return f"__luna_tmp_{hash_str}__"

    def _wrap_expr(self, node: ast.expr) -> ast.NamedExpr:
        # Do not instrument nodes that are being assigned to (Store) or deleted (Del)
        if hasattr(node, "ctx") and not isinstance(node.ctx, ast.Load):
            self.generic_visit(node)
            return node

        tmp = self._make_temp_var(node)
        self.generic_visit(node)
        
        # Save original location
        orig_col = getattr(node, "col_offset", None)
        orig_end_col = getattr(node, "end_col_offset", None)

        # Update node location so the inner expression has correct absolute column
        if orig_col is not None:
            node.col_offset += self.indent_offset
        if orig_end_col is not None:
            node.end_col_offset += self.indent_offset

        walrus_expr = ast.NamedExpr(
            target=ast.Name(id=tmp, ctx=ast.Store()),
            value=node
        )
        ast.copy_location(walrus_expr, node)
        ast.fix_missing_locations(walrus_expr)
        
        # Restore original location to walrus_expr so visit() can update it correctly
        if orig_col is not None:
            walrus_expr.col_offset = orig_col
        if orig_end_col is not None:
            walrus_expr.end_col_offset = orig_end_col
            
        return walrus_expr

    def visit(self, node: ast.Module):
        new_node = super().visit(node)
        if isinstance(new_node, ast.AST):
            if hasattr(new_node, "col_offset"):
                new_node.col_offset = new_node.col_offset + self.indent_offset
            if hasattr(new_node, "end_col_offset"):
                new_node.end_col_offset = new_node.end_col_offset + self.indent_offset
        return new_node

    def visit_BinOp(self, node: ast.BinOp):
        return self._wrap_expr(node)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        return self._wrap_expr(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        return self._wrap_expr(node)

    def visit_Compare(self, node: ast.Compare):
        return self._wrap_expr(node)

    def visit_Call(self, node: ast.Call):
        return self._wrap_expr(node)

    def visit_Subscript(self, node: ast.Subscript):
        return self._wrap_expr(node)

    def visit_Attribute(self, node: ast.Attribute):
        return self._wrap_expr(node)

    def visit_IfExp(self, node: ast.IfExp):
        return self._wrap_expr(node)

    def visit_List(self, node: ast.List):
        return self._wrap_expr(node)

    def visit_Dict(self, node: ast.Dict):
        return self._wrap_expr(node)

    def visit_Set(self, node: ast.Set):
        return self._wrap_expr(node)

    def visit_Tuple(self, node: ast.Tuple):
        return self._wrap_expr(node)

    def visit_ListComp(self, node: ast.ListComp):
        return self._wrap_expr(node)

    def visit_SetComp(self, node: ast.SetComp):
        return self._wrap_expr(node)

    def visit_DictComp(self, node: ast.DictComp):
        return self._wrap_expr(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        return self._wrap_expr(node)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        return self._wrap_expr(node)

    def visit_Lambda(self, node: ast.Lambda):
        return self._wrap_expr(node)

    def visit_JoinedStr(self, node: ast.JoinedStr):
        return self._wrap_expr(node)

    def visit_Yield(self, node):
        return self._wrap_expr(node)

    def visit_YieldFrom(self, node: ast.YieldFrom):
        return self._wrap_expr(node)

    def visit_Await(self, node):
        return self._wrap_expr(node)

    def visit_Assign(self, node: ast.Assign):
        node.value = self.visit(node.value)
        new_targets = []
        for target in node.targets:
            new_target = self.visit(target)
            new_targets.append(new_target)
        node.targets = new_targets
        return node

    def visit_AugAssign(self, node: ast.AugAssign):
        node.value = self.visit(node.value)
        node.target = self.visit(node.target)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign):
        node.value = self.visit(node.value) if node.value else None
        node.target = self.visit(node.target)
        node.annotation = self.visit(node.annotation)
        return node

    def visit_comprehension(self, node: ast.comprehension):
        # Assignment expressions are prohibited in the iterable expression of a comprehension
        # so we skip visiting node.iter
        self.visit(node.target)
        for i, if_node in enumerate(node.ifs):
            node.ifs[i] = self.visit(if_node)
        return node


class InstrumentingFinder(MetaPathFinder, Loader):
    _find_spec = importlib.machinery.PathFinder.find_spec

    def find_spec(
        self,
        name: str,
        path: Sequence[str | bytes] | None = None,
        target: types.ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        spec = self._find_spec(name, path, target)

        if (
            # the import machinery could not find a file to import
            spec is None
            # this is a namespace package (without `__init__.py`)
            # there's nothing to rewrite there
            or spec.origin is None
            # we can only rewrite source files
            or not isinstance(spec.loader, importlib.machinery.SourceFileLoader)
            # if the file doesn't exist, we can't rewrite it
            or not os.path.exists(spec.origin)
        ):
            return None

        spec.loader = self

        return spec

    def create_module(
        self, spec: importlib.machinery.ModuleSpec
    ) -> types.ModuleType | None:
        return None  # default behaviour is fine

    def exec_module(self, module: types.ModuleType) -> None:
        assert module.__spec__ is not None
        assert module.__spec__.origin is not None

        mod_path = Path(module.__spec__.origin)
        source = mod_path.read_bytes()

        try:
            tree = ast.parse(source, filename=mod_path)
        except SyntaxError as e:
            raise ValueError(f"Failed to parse module {module.__name__}: {e}")

        instrumentor = Instrumentor(tree)
        new_tree = instrumentor.run()

        try:
            code = compile(new_tree, filename=mod_path, mode="exec")
        except SyntaxError as e:
            raise ValueError(f"Failed to compile instrumented module {module.__name__}: {e}")
        exec(code, module.__dict__)

def _instrument_function(func: types.FunctionType) -> types.FunctionType:
    """Instrument a single function."""
    # Calculate indentation offset
    raw_source = inspect.getsource(func)
    indent_offset = len(raw_source) - len(raw_source.lstrip())
    
    source = textwrap.dedent(raw_source)
    filename = inspect.getsourcefile(func)
    first_line = func.__code__.co_firstlineno

    tree = ast.parse(source, filename=filename, mode="exec")
    new_tree = Instrumentor(tree, first_line, indent_offset).run()

    code = compile(new_tree, filename=filename, mode="exec")
    ns = {}
    exec(code, func.__globals__, ns)
    return ns[func.__name__]


def _instrument_class(cls: type) -> type:
    """Instrument a class."""
    raw_source = inspect.getsource(cls)
    indent_offset = len(raw_source) - len(raw_source.lstrip())

    source = textwrap.dedent(raw_source)
    filename = inspect.getsourcefile(cls)
    # getsourcelines returns (lines, starting_line_number)
    first_line = inspect.getsourcelines(cls)[1]

    tree = ast.parse(source, filename=filename, mode="exec")

    new_tree = Instrumentor(tree, first_line, indent_offset).run()

    code = compile(new_tree, filename=filename, mode="exec")
    ns = {}
    
    module_name = cls.__module__
    if module_name in sys.modules:
        global_ns = sys.modules[module_name].__dict__
    else:
        global_ns = {}
        for attr in cls.__dict__.values():
            if isinstance(attr, types.FunctionType):
                global_ns = attr.__globals__
                break
    
    exec(code, global_ns, ns)
    return ns[cls.__name__]


def run_instrument(
        target: types.FunctionType | types.ModuleType
) -> Union[types.FunctionType, types.ModuleType, type]:
    """
    Instrument a function, a module, or a class.
    """
    if isinstance(target, types.FunctionType):
        return _instrument_function(target)
    elif isinstance(target, type):
        return _instrument_class(target)
    else:
        raise TypeError(f"Unsupported type: {type(target)}")
