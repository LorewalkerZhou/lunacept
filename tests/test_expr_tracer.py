import sys
import types

import lunacept
from lunacept.instrumentor import run_instrument
from lunacept.parse import collect_frames

def find_node(nodes, expr):
    """Recursively find a node with the given expression"""
    for node in nodes:
        if node.expr == expr:
            return node
        found = find_node(node.children, expr)
        if found:
            return found
    return None

def get_trace_tree_from_exception(func):
    instrumented_func = run_instrument(func)
    try:
        instrumented_func()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        frames = collect_frames(exc_traceback)
        # The last frame is where the exception was raised
        return frames[-1].trace_tree
    return None

def test_constant():
    def target():
        raise ValueError(1)
    
    tree = get_trace_tree_from_exception(target)
    assert tree is not None
    
    const_node = find_node(tree, '1')
    # not catch constants
    assert const_node is None

def test_name():
    def target():
        a = 1
        raise ValueError(a)
    
    tree = get_trace_tree_from_exception(target)
    assert tree is not None
    
    name_node = find_node(tree, 'a')
    assert name_node is not None
    assert name_node.value == 1

def test_binop():
    def target():
        a = 1
        b = 2
        raise ValueError(a + b)
    
    tree = get_trace_tree_from_exception(target)
    assert tree is not None
    
    add_node = find_node(tree, 'a + b')
    assert add_node is not None
    assert add_node.value == 3
    
    a_node = find_node(add_node.children, 'a')
    assert a_node is not None
    assert a_node.value == 1
    
    b_node = find_node(add_node.children, 'b')
    assert b_node is not None
    assert b_node.value == 2

def test_call():
    def target():
        def foo(x):
            return x * 2
        val = 5
        raise ValueError(foo(val))

    tree = get_trace_tree_from_exception(target)
    
    call_node = find_node(tree, 'foo(val)')
    assert call_node is not None
    assert call_node.value == 10
    
    val_node = find_node(call_node.children, 'val')
    assert val_node is not None
    assert val_node.value == 5

def test_attribute():
    def target():
        class Obj:
            def __init__(self):
                self.x = 10
        o = Obj()
        raise ValueError(o.x)
        
    tree = get_trace_tree_from_exception(target)
    
    attr_node = find_node(tree, 'o.x')
    assert attr_node is not None
    assert attr_node.value == 10
    
    o_node = find_node(attr_node.children, 'o')
    assert o_node is not None
    assert isinstance(o_node.value, object)

def test_subscript():
    def target():
        lst = [1, 2, 3]
        idx = 1
        raise ValueError(lst[idx])
        
    tree = get_trace_tree_from_exception(target)
    
    sub_node = find_node(tree, 'lst[idx]')
    assert sub_node is not None
    assert sub_node.value == 2
    
    lst_node = find_node(sub_node.children, 'lst')
    assert lst_node.value == [1, 2, 3]
    
    idx_node = find_node(sub_node.children, 'idx')
    assert idx_node.value == 1

def test_unaryop():
    def target():
        a = 1
        raise ValueError(-a)

    tree = get_trace_tree_from_exception(target)

    unary_node = find_node(tree, '-a')
    assert unary_node is not None
    assert unary_node.value == -1

    a_node = find_node(unary_node.children, 'a')
    assert a_node is not None
    assert a_node.value == 1

def test_boolop():
    def target():
        t = True
        f = False
        raise ValueError(t and f)

    tree = get_trace_tree_from_exception(target)

    bool_node = find_node(tree, 't and f')
    assert bool_node is not None
    assert bool_node.value is False

    t_node = find_node(bool_node.children, 't')
    assert t_node is not None
    assert t_node.value is True

    f_node = find_node(bool_node.children, 'f')
    assert f_node is not None
    assert f_node.value is False

def test_compare():
    def target():
        x = 5
        y = 10
        raise ValueError(x < y)

    tree = get_trace_tree_from_exception(target)

    comp_node = find_node(tree, 'x < y')
    assert comp_node is not None
    assert comp_node.value is True

    x_node = find_node(comp_node.children, 'x')
    assert x_node.value == 5

    y_node = find_node(comp_node.children, 'y')
    assert y_node.value == 10

def test_list_literal():
    def target():
        a = 1
        b = 2
        raise ValueError([a, b])
        
    tree = get_trace_tree_from_exception(target)
    
    list_node = find_node(tree, '[a, b]')
    assert list_node is not None
    assert list_node.value == [1, 2]
    
    a_node = find_node(list_node.children, 'a')
    assert a_node.value == 1

    b_node = find_node(list_node.children, 'b')
    assert b_node.value == 2

def test_tuple_literal():
    def target():
        a = 1
        b = 2
        raise ValueError((a, b))
        
    tree = get_trace_tree_from_exception(target)
    
    tuple_node = find_node(tree, '(a, b)')
    assert tuple_node is not None
    assert tuple_node.value == (1, 2)
    
    a_node = find_node(tuple_node.children, 'a')
    assert a_node.value == 1
    
    b_node = find_node(tuple_node.children, 'b')
    assert b_node.value == 2    

def test_set_literal():
    def target():
        a = 1
        b = 2
        raise ValueError({a, b})
        
    tree = get_trace_tree_from_exception(target)
    
    set_node = find_node(tree, '{a, b}')
    assert set_node is not None
    assert set_node.value == {1, 2}
    
    a_node = find_node(set_node.children, 'a')
    assert a_node.value == 1
    
    b_node = find_node(set_node.children, 'b')
    assert b_node.value == 2

def test_dict_literal():
    def target():
        k = 'key'
        v = 'value'
        raise ValueError({k: v})
        
    tree = get_trace_tree_from_exception(target)
    
    dict_node = find_node(tree, '{k: v}')
    assert dict_node is not None
    assert dict_node.value == {'key': 'value'}

    k_node = find_node(dict_node.children, 'k')
    assert k_node.value == 'key'
    
    v_node = find_node(dict_node.children, 'v')
    assert v_node.value == 'value'

def test_ifexp():
    def target():
        a = 1
        b = 2
        c = 3
        raise ValueError(a if b else c)

    tree = get_trace_tree_from_exception(target)

    if_node = find_node(tree, 'a if b else c')
    assert if_node is not None
    assert if_node.value == 1

    a_node = find_node(if_node.children, 'a')
    assert a_node.value == 1

    b_node = find_node(if_node.children, 'b')
    assert b_node.value == 2

    c_node = find_node(if_node.children, 'c')
    assert c_node.value == 3

def test_lambda():
    def target():
        raise ValueError((lambda a: a + 1)(1))
        
    tree = get_trace_tree_from_exception(target)
    
    node = find_node(tree, '(lambda a: a + 1)(1)')
    assert node is not None
    assert node.value == 2

def test_namedexpr():
    def target():
        raise ValueError((a := 1))
        
    tree = get_trace_tree_from_exception(target)
    
    node = find_node(tree, '(a := 1)')
    assert node is not None
    assert node.value == 1

def test_joinedstr():
    def target():
        a = 1
        raise ValueError(f'hello {a}')
        
    tree = get_trace_tree_from_exception(target)
    
    node = find_node(tree, "f'hello {a}'")
    assert node is not None
    assert node.value == 'hello 1'

def test_starred():
    def target():
        a = [1, 2, 3]
        raise ValueError([*a])
        
    tree = get_trace_tree_from_exception(target)
    
    node = find_node(tree, '[*a]')
    assert node is not None
    assert node.value == [1, 2, 3]

def test_list_comp():
    def target():
        nums = [1, 2, 3]
        raise ValueError([n * 2 for n in nums])
        
    tree = get_trace_tree_from_exception(target)
    
    comp_node = find_node(tree, '[n * 2 for n in nums]')
    assert comp_node is not None
    assert comp_node.value == [2, 4, 6]

def test_set_comp():
    def target():
        nums = [1, 2, 3]
        raise ValueError({n * 2 for n in nums})
        
    tree = get_trace_tree_from_exception(target)
    
    comp_node = find_node(tree, '{n * 2 for n in nums}')
    assert comp_node is not None
    assert comp_node.value == {2, 4, 6}

def test_dict_comp():
    def target():
        nums = [1, 2, 3]
        raise ValueError({n: n * 2 for n in nums})
        
    tree = get_trace_tree_from_exception(target)
    
    comp_node = find_node(tree, '{n: n * 2 for n in nums}')
    assert comp_node is not None
    assert comp_node.value == {1: 2, 2: 4, 3: 6}


def test_assignment():
    def target():
        class A:
            def __init__(self):
                self.x = [1, 2, 3]

        a = A()
        a.x[4] = 4

    tree = get_trace_tree_from_exception(target)
    assert tree is not None

    assign_node = find_node(tree, 'a.x')
    assert assign_node is not None
    assert assign_node.value == [1, 2, 3]

    a_node = assign_node.children[0]
    assert a_node is not None
    assert isinstance(a_node.value, object)

def test_augassign():
    def target():
        class A:
            def __init__(self):
                self.x = [1, 2, 3]
        a = A()
        a.x[0] += "s"

    tree = get_trace_tree_from_exception(target)
    assert tree is not None

    target_node = find_node(tree, 'a.x[0]')
    assert target_node is not None
    assert target_node.value == "<left value>"

    a_x_node = target_node.children[0]
    assert a_x_node is not None
    assert a_x_node.value == [1, 2, 3]

    a_node = a_x_node.children[0]
    assert a_node is not None
    assert isinstance(a_node.value, object)

def test_annassign():
    def target():
        class A:
            def __init__(self):
                self.x = [1, 2, 3]

        a = A()
        a.x[4]: int = 4

    tree = get_trace_tree_from_exception(target)
    assert tree is not None

    assign_node = find_node(tree, 'a.x')
    assert assign_node is not None
    assert assign_node.value == [1, 2, 3]

    a_node = assign_node.children[0]
    assert a_node is not None
    assert isinstance(a_node.value, object)

def test_multiline():
    def target():
        a = 1
        b = 2
        raise ValueError((a /
                          b))

    tree = get_trace_tree_from_exception(target)
    assert tree is not None

    # Depending on how unparse works, it might put it on one line
    # ast.unparse usually produces 'a / b'
    binop_node = find_node(tree, 'a / b')
    assert binop_node is not None
    assert binop_node.value == 0.5

    a_node = find_node(binop_node.children, 'a')
    assert a_node.value == 1

    b_node = find_node(binop_node.children, 'b')
    assert b_node.value == 2

def test_yield():
    def target():
        def gen():
            raise ValueError((yield 1))
            
        g = gen()
        next(g)
        g.send(10)

    tree = get_trace_tree_from_exception(target)
    assert tree is not None
    
    yield_node = find_node(tree, '(yield 1)')
    assert yield_node is not None
    assert yield_node.value == 10

def test_yield_from():
    def target():
        def subgen():
            yield 1
            return 2
            
        def gen():
            raise ValueError((yield from subgen()) + 1)
            
        g = gen()
        next(g) 
        g.send(2)

    tree = get_trace_tree_from_exception(target)
    assert tree is not None
    
    yf_node = find_node(tree, '(yield from subgen())')
    assert yf_node is not None
    assert yf_node.value == 2