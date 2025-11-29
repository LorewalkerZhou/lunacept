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
        if node.id.startswith("__luna_tmp_") or node.id.startswith("_luna_tmp_"):
            node.id = self._get_new_name(node.id)
        return node

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)
        for i, target in enumerate(node.targets):
            if isinstance(target, ast.Name) and (target.id.startswith("__luna_tmp_") or target.id.startswith("_luna_tmp_")):
                node.targets[i].id = self._get_new_name(target.id)
        return node
    
    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.generic_visit(node)
        if isinstance(node.target, ast.Name) and (node.target.id.startswith("__luna_tmp_") or node.target.id.startswith("_luna_tmp_")):
            node.target.id = self._get_new_name(node.target.id)
        return node

def normalize_ast(tree):
    replacer = TempVarReplacer()
    return replacer.visit(tree)

def test_constant():
    code_str = "x = 1"
    new_tree = transform_code(code_str)

    expected_code = """
x = 1
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))


def test_name():
    code_str = "x = a"
    new_tree = transform_code(code_str)

    expected_code = """
x = a
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_binop():
    code_str = "x = a + b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a + b)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_call():
    code_str = "x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_attribute():
    code_str = "x = a.b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a.b)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_subscript():
    code_str = "x = a[b]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a[b])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_unaryop():
    code_str = "x = -a"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := -a)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_boolop():
    code_str = "x = a and b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a and b)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_compare():
    code_str = "x = a < b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a < b)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_list_literal():
    code_str = "x = [1, 2]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := [1, 2])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_tuple_literal():
    code_str = "x = (1, 2)"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := (1, 2))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_set_literal():
    code_str = "x = {1, 2}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := {1, 2})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_dict_literal():
    code_str = "x = {'a': 1}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := {'a': 1})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_ifexp():
    code_str = "x = a if b else c"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := a if b else c)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_lambda():
    code_str = "x = lambda a: a"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := lambda a: a)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_namedexpr():
    code_str = "x = (a := 1)"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := (a := 1))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_joinedstr():
    code_str = 'x = f"hello {a}"'
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := f"hello {a}")
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_listcomp():
    code_str = "x = [i for i in range(10)]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := [i for i in range(10)])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_setcomp():
    code_str = "x = {i for i in range(10)}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := {i for i in range(10)})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_dictcomp():
    code_str = "x = {i: i for i in range(10)}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := {i: i for i in range(10)})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_generatorexp():
    code_str = "x = (i for i in range(10))"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := (i for i in range(10)))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_left_in_binop():
    code_str = "x = f() + a"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (__luna_tmp_0 := f()) + a)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_right_in_binop():
    code_str = "x = a + f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a + (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_operand_in_unaryop():
    code_str = "x = -f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (-(__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_left_in_boolop():
    code_str = "x = f() and a"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := ((__luna_tmp_0 := f()) and a))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_right_in_boolop():
    code_str = "x = a and f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a and (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_left_in_compare():
    code_str = "x = f() < a"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := ((__luna_tmp_0 := f()) < a))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_comparators_0_in_compare():
    code_str = "x = a < f() < b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a < (__luna_tmp_0 := f()) < b))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_comparators_1_in_compare():
    code_str = "x = a < b < f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a < b < (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_func_in_call():
    code_str = "x = g()()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (__luna_tmp_0 := g())())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_args_in_call():
    code_str = "x = f(a, g())"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := f(a, (__luna_tmp_0 := g())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_kwargs_in_call():
    code_str = "x = f(a=g())"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := f(a=(__luna_tmp_0 := g())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_attribute():
    code_str = "x = f().attr"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (__luna_tmp_0 := f()).attr)
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_subscript():
    code_str = "x = f()[a]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (__luna_tmp_0 := f())[a])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_slice_in_subscript():
    code_str = "x = a[f()]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := a[(__luna_tmp_0 := f())])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_lower_in_slice():
    code_str = "x = a[f(): b]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := a[(__luna_tmp_0 := f()): b])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_upper_in_slice():
    code_str = "x = a[b: f()]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := a[b: (__luna_tmp_0 := f())])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_step_in_slice():
    code_str = "x = a[b: f(): c]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := a[b: (__luna_tmp_0 := f()): c])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_ifexp():
    code_str = "x = f() if a else b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := ((__luna_tmp_0 := f()) if a else b))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_test_in_ifexp():
    code_str = "x = a if f() else b"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a if (__luna_tmp_0 := f()) else b))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_orelse_in_ifexp():
    code_str = "x = a if b else f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a if b else (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_element_in_list():
    code_str = "x = [f(), a]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := [(__luna_tmp_0 := f()), a])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_element_in_tuple():
    code_str = "x = (f(), a)"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := ((__luna_tmp_0 := f()), a))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_element_in_set():
    code_str = "x = {f(), a}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {(__luna_tmp_0 := f()), a})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_key_in_dict():
    code_str = "x = {f(): a}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {(__luna_tmp_0 := f()): a})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_dict():
    code_str = "x = {a: f()}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {a: (__luna_tmp_0 := f())})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_starred():
    code_str = "x = [*f()]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := [*(__luna_tmp_0 := f())])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_joinedstr():
    code_str = 'x = f"hello {f()}"'
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := f"hello {(__luna_tmp_0 := f())}")
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_lambda():
    code_str = "x = lambda a: f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := lambda a: (__luna_tmp_0 := f()))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_namedexpr():
    code_str = "x = (a := f())"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (a := (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_elt_in_listcomp():
    code_str = "x = [f() for i in range(10)]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := [(__luna_tmp_0 := f()) for i in range(10)])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_elt_in_setcomp():
    code_str = "x = {f() for i in range(10)}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {(__luna_tmp_0 := f()) for i in range(10)})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_key_in_dictcomp():
    code_str = "x = {f(): i for i in range(10)}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {(__luna_tmp_0 := f()): i for i in range(10)})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_value_in_dictcomp():
    code_str = "x = {i: f() for i in range(10)}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {i: (__luna_tmp_0 := f()) for i in range(10)})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_elt_in_generatorexp():
    code_str = "x = (f() for i in range(10))"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := ((__luna_tmp_0 := f()) for i in range(10)))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_if_in_listcomp():
    code_str = "x = [i for i in range(10) if f()]"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := [i for i in range(10) if (__luna_tmp_0 := f())])
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_if_in_setcomp():
    code_str = "x = {i for i in range(10) if f()}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {i for i in range(10) if (__luna_tmp_0 := f())})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_if_in_dictcomp():
    code_str = "x = {i: i for i in range(10) if f()}"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := {i: i for i in range(10) if (__luna_tmp_0 := f())})
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_if_in_generatorexp():
    code_str = "x = (i for i in range(10) if f())"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_1 := (i for i in range(10) if (__luna_tmp_0 := f())))
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_assign():
    code_str = "x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_augassign():
    code_str = "x += f()"
    new_tree = transform_code(code_str)

    expected_code = """
x += (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_annassign():
    code_str = "x: int = f()"
    new_tree = transform_code(code_str)

    expected_code = """
x: int = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_annassign_without_value():
    code_str = "x: int"
    new_tree = transform_code(code_str)

    expected_code = """
x: int
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_return():
    code_str = "return f()"
    new_tree = transform_code(code_str)

    expected_code = """
return (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_test_in_if():
    code_str = """
if f(): 
    x = 1
    """
    new_tree = transform_code(code_str)

    expected_code = """
if (__luna_tmp_0 := f()): 
    x = 1
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_if():
    code_str = "if a: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
if a: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_orelse_in_if():
    code_str = "if a: x = 1\nelse: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
if a: x = 1
else: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_iter_in_for():
    code_str = "for i in f(): pass"
    new_tree = transform_code(code_str)

    expected_code = """
for i in (__luna_tmp_0 := f()): pass
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_for():
    code_str = "for i in range(10): x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
for i in (__luna_tmp_0 := range(10)): x = (__luna_tmp_1 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_orelse_in_for():
    code_str = "for i in range(10): pass\nelse: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
for i in (__luna_tmp_0 := range(10)): pass
else: x = (__luna_tmp_1 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_test_in_while():
    code_str = "while f(): pass"
    new_tree = transform_code(code_str)

    expected_code = """
while (__luna_tmp_0 := f()): pass
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_while():
    code_str = "while a: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
while a: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_orelse_in_while():
    code_str = "while a: pass\nelse: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
while a: pass
else: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_test_in_assert():
    code_str = "assert f()"
    new_tree = transform_code(code_str)

    expected_code = """
assert (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_msg_in_assert():
    code_str = "assert a, f()"
    new_tree = transform_code(code_str)

    expected_code = """
assert a, (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_context_expr_in_with():
    code_str = "with f(): x = 1"
    new_tree = transform_code(code_str)

    expected_code = """
with (__luna_tmp_0 := f()): x = 1
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_with():
    code_str = "with open('file'): x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
with (__luna_tmp_0 := open('file')): x = (__luna_tmp_1 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_exc_in_raise():
    code_str = "raise f()"
    new_tree = transform_code(code_str)

    expected_code = """
raise (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_cause_in_raise():
    code_str = "raise Exception from f()"
    new_tree = transform_code(code_str)

    expected_code = """
raise Exception from (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_target_in_delete():
    code_str = "del a[f()]"
    new_tree = transform_code(code_str)

    expected_code = """
del a[(__luna_tmp_0 := f())]
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_try():
    code_str = "try: x = f()\nexcept: pass"
    new_tree = transform_code(code_str)

    expected_code = """
try: x = (__luna_tmp_0 := f())
except: pass
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_type_in_except():
    code_str = "try: pass\nexcept f(): pass"
    new_tree = transform_code(code_str)

    expected_code = """
try: pass
except (__luna_tmp_0 := f()): pass
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_body_in_except():
    code_str = "try: pass\nexcept: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
try: pass
except: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_orelse_in_try():
    code_str = "try: pass\nexcept: pass\nelse: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
try: pass
except: pass
else: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))

def test_finalbody_in_try():
    code_str = "try: pass\nexcept: pass\nfinally: x = f()"
    new_tree = transform_code(code_str)

    expected_code = """
try: pass
except: pass
finally: x = (__luna_tmp_0 := f())
"""
    expected_tree = ast.parse(expected_code.strip())
    assert ast.dump(normalize_ast(new_tree)) == ast.dump(normalize_ast(expected_tree))