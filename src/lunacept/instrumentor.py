#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : instrumentor.py
@Author  : LorewalkerZhou
@Time    : 2025/8/31 16:35
@Desc    : 
"""
import ast
import inspect
import types
from _ast import expr

class Instrumentor(ast.NodeTransformer):
    def __init__(self, first_line):
        super().__init__()
        self.first_line = first_line

    def _make_temp_var(self, node: expr):
        expr_str = ast.unparse(node)
        lineno = node.lineno + self.first_line - 1
        end_lineno = (node.end_lineno if node.end_lineno else lineno) + self.first_line - 1
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset

        import hashlib
        ori_str = f"{expr_str}-{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"
        hash_str = hashlib.md5(ori_str.encode()).hexdigest()[0:12]
        return f"__luna_tmp_{hash_str}"

    def _instrument_expr(self, expr):
        if isinstance(expr, ast.BinOp):
            left_stmts, left_expr = self._instrument_expr(expr.left)
            right_stmts, right_expr = self._instrument_expr(expr.right)
            new_expr = ast.BinOp(left=left_expr, op=expr.op, right=right_expr)
            tmp = self._make_temp_var(expr)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_expr
            )
            ast.copy_location(assign_node, expr)
            ast.fix_missing_locations(assign_node)
            return left_stmts + right_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(expr, ast.Call):
            all_stmts = []
            new_args = []

            for arg in expr.args:
                arg_stmts, arg_expr = self._instrument_expr(arg)
                all_stmts.extend(arg_stmts)
                new_args.append(arg_expr)

            new_call = ast.Call(func=expr.func, args=new_args, keywords=expr.keywords)

            tmp = self._make_temp_var(expr)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_call
            )
            ast.copy_location(assign_node, expr)
            ast.fix_missing_locations(assign_node)

            return all_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        return [], expr

    def visit_Assign(self, node: ast.Assign):
        pre_stmts, new_value = self._instrument_expr(node.value)
        new_assign = ast.Assign(targets=node.targets, value=new_value)
        ast.copy_location(new_assign, node)
        ast.fix_missing_locations(new_assign)
        return pre_stmts + [new_assign]

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            return node
        pre_stmts, new_value = self._instrument_expr(node.value)
        new_ret = ast.Return(value=new_value)
        ast.copy_location(new_ret, node)
        ast.fix_missing_locations(new_ret)
        return pre_stmts + [new_ret]

    def visit_Expr(self, node: ast.Expr):
        self.generic_visit(node)
        pre_stmts, new_value = self._instrument_expr(node.value)
        return pre_stmts or node


def run_instrument(
        func: types.FunctionType
) -> types.FunctionType:
    """Replace a function with an instrumented version"""
    source = inspect.getsource(func)
    filename = inspect.getsourcefile(func)
    first_line = func.__code__.co_firstlineno

    tree = ast.parse(source, filename=filename, mode="exec")
    new_tree = Instrumentor(first_line).visit(tree)
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
    ast.increment_lineno(new_tree, first_line - 1)

    code = compile(new_tree, filename=filename, mode="exec")
    ns = {}
    exec(code, func.__globals__, ns)
    return ns[func.__name__]