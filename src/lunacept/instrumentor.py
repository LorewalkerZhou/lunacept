#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : instrumentor.py
@Author  : LorewalkerZhou
@Time    : 2025/8/31 16:35
@Desc    : 
"""
import _ast
import ast
import inspect
import types

class Instrumentor(ast.NodeTransformer):
    def __init__(self, first_line):
        super().__init__()
        self.first_line = first_line

    def _make_temp_var(self, node: _ast.expr):
        expr_str = ast.unparse(node)
        lineno = node.lineno
        end_lineno = node.end_lineno if node.end_lineno else lineno
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset

        lineno += self.first_line - 1
        end_lineno += self.first_line - 1

        import hashlib
        ori_str = f"{expr_str}-{lineno}-{end_lineno}-{col_offset}-{end_col_offset}"
        hash_str = hashlib.md5(ori_str.encode()).hexdigest()[0:12]
        return f"__luna_tmp_{hash_str}"

    def _instrument_expr(self, node: _ast.expr):
        if isinstance(node, ast.BinOp):
            left_stmts, left_expr = self._instrument_expr(node.left)
            right_stmts, right_expr = self._instrument_expr(node.right)
            new_expr = ast.BinOp(left=left_expr, op=node.op, right=right_expr)
            tmp = self._make_temp_var(node)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_expr
            )
            ast.copy_location(assign_node, node)
            ast.fix_missing_locations(assign_node)
            return left_stmts + right_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(node, ast.UnaryOp):
            operand_stmts, operand_expr = self._instrument_expr(node.operand)

            new_expr = ast.UnaryOp(op=node.op, operand=operand_expr)
            ast.copy_location(new_expr, node)
            ast.fix_missing_locations(new_expr)

            tmp = self._make_temp_var(node)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_expr
            )
            ast.copy_location(assign_node, node)
            ast.fix_missing_locations(assign_node)

            return operand_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            left_stmts, left_expr = self._instrument_expr(node.values[0])

            tmp_result = self._make_temp_var(node)

            if_body = []
            else_body = []

            right_stmts, right_expr = self._instrument_expr(node.values[1])
            if_body.extend(right_stmts)
            if_body.append(ast.Assign(
                targets=[ast.Name(id=tmp_result, ctx=ast.Store())],
                value=right_expr
            ))

            else_body.append(ast.Assign(
                targets=[ast.Name(id=tmp_result, ctx=ast.Store())],
                value=left_expr
            ))

            if_node = ast.If(
                test=left_expr,
                body=if_body,
                orelse=else_body
            )
            ast.copy_location(if_node, node)
            ast.fix_missing_locations(if_node)

            return left_stmts + [if_node], ast.Name(id=tmp_result, ctx=ast.Load())

        elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            left_stmts, left_expr = self._instrument_expr(node.values[0])

            tmp_result = self._make_temp_var(node)

            if_body = []
            else_body = []

            right_stmts, right_expr = self._instrument_expr(node.values[1])
            else_body.extend(right_stmts)
            else_body.append(ast.Assign(
                targets=[ast.Name(id=tmp_result, ctx=ast.Store())],
                value=right_expr
            ))

            if_body.append(ast.Assign(
                targets=[ast.Name(id=tmp_result, ctx=ast.Store())],
                value=left_expr
            ))

            if_node = ast.If(
                test=left_expr,
                body=if_body,
                orelse=else_body
            )
            ast.copy_location(if_node, node)
            ast.fix_missing_locations(if_node)

            return left_stmts + [if_node], ast.Name(id=tmp_result, ctx=ast.Load())

        elif isinstance(node, ast.Compare):
            left_stmts, left_expr = self._instrument_expr(node.left)

            all_stmts = left_stmts
            comparators_exprs = []

            for comp in node.comparators:
                comp_stmts, comp_expr = self._instrument_expr(comp)
                all_stmts.extend(comp_stmts)
                comparators_exprs.append(comp_expr)

            new_compare = ast.Compare(
                left=left_expr,
                ops=node.ops,
                comparators=comparators_exprs
            )

            tmp = self._make_temp_var(node)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_compare
            )
            ast.copy_location(assign_node, node)
            ast.fix_missing_locations(assign_node)

            return all_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(node, ast.Call):
            all_stmts = []
            new_args = []

            for arg in node.args:
                arg_stmts, arg_expr = self._instrument_expr(arg)
                all_stmts.extend(arg_stmts)
                new_args.append(arg_expr)

            new_call = ast.Call(func=node.func, args=new_args, keywords=node.keywords)

            tmp = self._make_temp_var(node)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_call
            )
            ast.copy_location(assign_node, node)
            ast.fix_missing_locations(assign_node)

            return all_stmts + [assign_node], ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(node, ast.Subscript):
            value_stmts, value_expr = self._instrument_expr(node.value)
            slice_stmts, slice_expr = self._instrument_expr(node.slice)

            new_subscript = ast.Subscript(
                value=value_expr,
                slice=slice_expr,
                ctx=node.ctx
            )
            ast.copy_location(new_subscript, node)
            ast.fix_missing_locations(new_subscript)

            tmp = self._make_temp_var(node)
            assign_node = ast.Assign(
                targets=[ast.Name(id=tmp, ctx=ast.Store())],
                value=new_subscript
            )
            ast.copy_location(assign_node, node)
            ast.fix_missing_locations(assign_node)

            all_stmts = value_stmts + slice_stmts + [assign_node]
            return all_stmts, ast.Name(id=tmp, ctx=ast.Load())

        elif isinstance(node, ast.Slice):
            lower_stmts, lower_expr = self._instrument_expr(node.lower) if node.lower else ([], None)
            upper_stmts, upper_expr = self._instrument_expr(node.upper) if node.upper else ([], None)
            step_stmts, step_expr = self._instrument_expr(node.step) if node.step else ([], None)

            new_slice = ast.Slice(lower=lower_expr, upper=upper_expr, step=step_expr)
            ast.copy_location(new_slice, node)
            ast.fix_missing_locations(new_slice)

            return lower_stmts + upper_stmts + step_stmts, new_slice

        elif isinstance(node, ast.IfExp):
            cond_stmts, cond_expr = self._instrument_expr(node.test)

            body_stmts, body_expr = self._instrument_expr(node.body)
            tmp_if = self._make_temp_var(node)
            body_assign = ast.Assign(targets=[ast.Name(id=tmp_if, ctx=ast.Store())], value=body_expr)
            ast.copy_location(body_assign, node.body)
            ast.fix_missing_locations(body_assign)
            body_stmts.append(body_assign)

            orelse_stmts, orelse_expr = self._instrument_expr(node.orelse)
            orelse_assign = ast.Assign(targets=[ast.Name(id=tmp_if, ctx=ast.Store())], value=orelse_expr)
            ast.copy_location(orelse_assign, node.orelse)
            ast.fix_missing_locations(orelse_assign)
            orelse_stmts.append(orelse_assign)

            if_node = ast.If(
                test=cond_expr,
                body=body_stmts,
                orelse=orelse_stmts
            )
            ast.copy_location(if_node, node)
            ast.fix_missing_locations(if_node)

            return cond_stmts + [if_node], ast.Name(id=tmp_if, ctx=ast.Load())

        return [], node

    def visit_Expr(self, node: ast.Expr):
        pre_stmts, new_value = self._instrument_expr(node.value)
        return pre_stmts or node

    def visit_Assign(self, node: ast.Assign):
        pre_stmts, new_value = self._instrument_expr(node.value)
        new_assign = ast.Assign(targets=node.targets, value=new_value)
        ast.copy_location(new_assign, node)
        ast.fix_missing_locations(new_assign)
        return pre_stmts + [new_assign]

    def visit_AugAssign(self, node: ast.AugAssign):
        pre_stmts, new_value = self._instrument_expr(node.value)
        new_node = ast.AugAssign(
            target=node.target,
            op=node.op,
            value=new_value
        )
        ast.copy_location(new_node, node)
        ast.fix_missing_locations(new_node)
        return pre_stmts + [new_node]

    def visit_Return(self, node: ast.Return):
        if node.value is None:
            return node
        pre_stmts, new_value = self._instrument_expr(node.value)
        new_ret = ast.Return(value=new_value)
        ast.copy_location(new_ret, node)
        ast.fix_missing_locations(new_ret)
        return pre_stmts + [new_ret]

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        pre_stmts, new_test = self._instrument_expr(node.test)
        node.test = new_test
        return pre_stmts + [node]

    def visit_While(self, node: ast.While):
        self.generic_visit(node)
        cond_stmts, cond_expr = self._instrument_expr(node.test)
        new_while = ast.While(
            test=cond_expr,
            body=node.body + cond_stmts,
            orelse=node.orelse
        )
        ast.copy_location(new_while, node)
        ast.fix_missing_locations(new_while)
        return cond_stmts + [new_while]

    def visit_With(self, node: ast.With):
        new_items = []
        pre_stmts = []

        for item in node.items:
            ctx_stmts, ctx_expr = self._instrument_expr(item.context_expr)
            pre_stmts.extend(ctx_stmts)

            new_item = ast.withitem(
                context_expr=ctx_expr,
                optional_vars=item.optional_vars
            )
            new_items.append(new_item)

        new_body = []
        for stmt in node.body:
            result = self.visit(stmt)
            if isinstance(result, list):
                new_body.extend(result)
            else:
                new_body.append(result)

        new_with = ast.With(items=new_items, body=new_body)
        ast.copy_location(new_with, node)
        ast.fix_missing_locations(new_with)

        return pre_stmts + [new_with]

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