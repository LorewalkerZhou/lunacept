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
        self.mapping: dict[str, str] = {}  # 原始 -> 新临时变量名映射

    def _get_new_name(self, old_name: str) -> str:
        if old_name not in self.mapping:
            new_name = f"__luna_test_tmp_{self.temp_var_counter}"
            self.mapping[old_name] = new_name
            self.temp_var_counter += 1
        return self.mapping[old_name]

    def visit_Name(self, node: ast.Name):
        if node.id.startswith("__luna_tmp_"):
            node.id = self._get_new_name(node.id)
        return node

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)
        for i, target in enumerate(node.targets):
            if isinstance(target, ast.Name) and target.id.startswith("__luna_tmp_"):
                node.targets[i].id = self._get_new_name(target.id)
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

def test_subscribe_with_function_call():
    code_str = "output = d[f()]"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
__luna_tmp_1 = d[__luna_tmp_0]
output = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_nested_subscribe_with_function_call():
    code_str = "output = d[f()][g()]"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
__luna_tmp_1 = d[__luna_tmp_0]
__luna_tmp_2 = g()
__luna_tmp_3 = __luna_tmp_1[__luna_tmp_2]
output = __luna_tmp_3
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_slice_with_function_call():
    code_str = "output = d[f():g()]"
    new_tree = transform_code(code_str)

    print(ast.unparse(new_tree))

    expected_code = """
__luna_tmp_0 = f()
__luna_tmp_1 = g()
__luna_tmp_2 = d[__luna_tmp_0:__luna_tmp_1]
output = __luna_tmp_2
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_nested_slice_with_function_call():
    code_str = "output = d[f():g()][h():k()]"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
__luna_tmp_1 = g()
__luna_tmp_2 = d[__luna_tmp_0:__luna_tmp_1]
__luna_tmp_3 = h()
__luna_tmp_4 = k()
__luna_tmp_5 = __luna_tmp_2[__luna_tmp_3:__luna_tmp_4]
output = __luna_tmp_5
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_unaryop_with_function_call():
    code_str = "output = -f()"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
__luna_tmp_1 = -__luna_tmp_0
output = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_boolop_and_with_function_call():
    code_str = "output = f() and g()"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
if __luna_tmp_0:
    __luna_tmp_1 = g()
    __luna_tmp_2 = __luna_tmp_1
else:
    __luna_tmp_2 = __luna_tmp_0
output = __luna_tmp_2
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_boolop_or_with_function_calls():
    code_str = "output = f() or g()"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
if __luna_tmp_0:
    __luna_tmp_1 = __luna_tmp_0
else:
    __luna_tmp_2 = g()
    __luna_tmp_1 = __luna_tmp_2
output = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_ifexp_with_function_calls():
    code_str = "output = f1() if f2() else f3()"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f2()
if __luna_tmp_0:
    __luna_tmp_1 = f1()
    __luna_tmp_3 = __luna_tmp_1
else:
    __luna_tmp_2 = f3()
    __luna_tmp_3 = __luna_tmp_2
output = __luna_tmp_3
"""
    expected_tree = ast.parse(expected_code.strip())
    print()
    print(ast.unparse(normalize_ast(new_tree)))
    print(ast.unparse(normalize_ast(expected_tree)))

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_compare_with_function_call():
    code_str = "output = a < b <= f(c)"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f(c)
__luna_tmp_1 = a < b <= __luna_tmp_0
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

def test_augassign_with_function_call():
    code_str = "a += f(b)"
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f(b)
a += __luna_tmp_0
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_if_with_function_call():
    code_str = """
if f(a):
    b = g(a)
else:
    b = h(a)
"""
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f(a)
if __luna_tmp_0:
    __luna_tmp_1 = g(a)
    b = __luna_tmp_1
else:
    __luna_tmp_2 = h(a)
    b = __luna_tmp_2
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.unparse(normalize_ast(new_tree)) == ast.unparse(normalize_ast(expected_tree))

def test_while_with_function_call():
    code_str = """
while f(a):
    a = g(a)
"""
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f(a)
while __luna_tmp_0:
    __luna_tmp_1 = g(a)
    a = __luna_tmp_1
    __luna_tmp_0 = f(a)
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.unparse(normalize_ast(new_tree)) == ast.unparse(normalize_ast(expected_tree))

def test_for_with_function_call():
    code_str = """
for i in range(n):
    a = x / f(i)
"""
    new_tree = transform_code(code_str)

    expected_code = """
for i in range(n):
    __luna_tmp_0 = f(i)
    __luna_tmp_1 = x / __luna_tmp_0
    a = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.unparse(normalize_ast(new_tree)) == ast.unparse(normalize_ast(expected_tree))

def test_with_with_function_call_context():
    code_str = """
with f() as resource:
    a = g(resource)
"""
    new_tree = transform_code(code_str)

    expected_code = """
__luna_tmp_0 = f()
with __luna_tmp_0 as resource:
    __luna_tmp_1 = g(resource)
    a = __luna_tmp_1
"""
    expected_tree = ast.parse(expected_code.strip())

    assert ast.unparse(normalize_ast(new_tree)) == ast.unparse(normalize_ast(expected_tree))
