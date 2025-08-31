#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : test_instrumentor.py
@Author  : LorewalkerZhou
@Time    : 2025/8/31 17:04
@Desc    : 
"""
import ast
from lunacept.instrumentor import Instrumentor

def transform_code(code_str, first_line=1):
    tree = ast.parse(code_str)
    instrumentor = Instrumentor(first_line=first_line)
    new_tree = instrumentor.visit(tree)
    return new_tree

class TempVarReplacer(ast.NodeTransformer):
    def __init__(self):
        self.temp_var_counter = 0

    def visit_Name(self, node):
        if node.id.startswith("__luna_tmp_"):
            node.id = f"__luna_tmp_{self.temp_var_counter}"
            self.temp_var_counter += 1
        return node

    def visit_Assign(self, node):
        self.generic_visit(node)
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.startswith("__luna_tmp_"):
                target.id = f"__luna_tmp_{self.temp_var_counter}"
                self.temp_var_counter += 1
        return node

def normalize_ast(tree):
    replacer = TempVarReplacer()
    return replacer.visit(tree)

def test_simple_expression_with_function_call():
    code_str = "output = fun() / a"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = fun()
__luna_tmp_1 = __luna_tmp_0 / a
output = __luna_tmp_1
    """
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_multiline_expression_with_function_call():
    code_str = "output = fun() /\\\n a"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = fun()
__luna_tmp_1 = __luna_tmp_0 / a
output = __luna_tmp_1
    """
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))


def test_complex_expression_with_function_call():
    code_str = "output = func1(arg1, func2(arg2))"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = func2(arg2)
__luna_tmp_1 = func1(arg1, __luna_tmp_0)
output = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_return_statement_with_function_call():
    code_str = "def my_func():\n    return get_value() / 2"
    new_tree = transform_code(code_str)

    expected_code = """
def my_func():
    __luna_tmp_0 = get_value()
    __luna_tmp_1 = __luna_tmp_0 / 2
    return __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))
