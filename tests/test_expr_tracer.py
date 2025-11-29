import sys
import pytest
from lunacept.instrumentor import run_instrument
from lunacept.parse import collect_frames, TraceNode, build_trace_tree
import linecache

def find_node(nodes, expr):
    """Recursively find a node with the given expression"""
    for node in nodes:
        if node.expr == expr:
            return node
        found = find_node(node.children, expr)
        if found:
            return found
    return None

def test_simple_addition():
    def target():
        a = 1
        b = 2
        c = a + b + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        # Build trace tree for the whole line
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        # Find the node for 'a + b'
        add_node = find_node(trace_tree, 'a + b')
        assert add_node is not None
        assert add_node.value == 3
        assert len(add_node.children) == 2
        assert add_node.children[0].expr == 'a'
        assert add_node.children[0].value == 1
        assert add_node.children[1].expr == 'b'
        assert add_node.children[1].value == 2

def test_list_comprehension():
    def target():
        nums = [1, 2, 3]
        squares = [x * x for x in nums] + [1 / 0]

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        # Check if list comp result is traced
        comp_node = find_node(trace_tree, '[x * x for x in nums]')
        assert comp_node is not None
        assert comp_node.value == [1, 4, 9]

def test_function_call():
    def target():
        def add(x, y):
            return x + y
        x = 10
        y = 20
        res = add(x, y) + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        call_node = find_node(trace_tree, 'add(x, y)')
        assert call_node is not None
        assert call_node.value == 30
        assert len(call_node.children) > 0 # Should trace args

def test_unary_op():
    def target():
        a = 10
        b = -a + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        unary_node = find_node(trace_tree, '-a')
        assert unary_node is not None
        assert unary_node.value == -10
        assert unary_node.children[0].expr == 'a'
        assert unary_node.children[0].value == 10

def test_bool_op():
    def target():
        a = True
        b = False
        c = (a and b) or (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        # 'a and b' should be False
        bool_node = find_node(trace_tree, 'a and b')
        assert bool_node is not None
        assert bool_node.value == False

def test_compare():
    def target():
        a = 10
        b = 20
        c = (a < b) == (1 / 0) # This might not trigger div by zero if (a < b) is False? No, == evaluates both.
        # Wait, (a < b) is True. True == (1/0).
        # To be safe, let's use + 
        c = (a < b) + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        comp_node = find_node(trace_tree, 'a < b')
        assert comp_node is not None
        assert comp_node.value == True

def test_subscript():
    def target():
        a = [10, 20, 30]
        b = a[1] + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        sub_node = find_node(trace_tree, 'a[1]')
        assert sub_node is not None
        assert sub_node.value == 20

def test_attribute():
    def target():
        class Point:
            def __init__(self, x, y):
                self.x = x
                self.y = y
        p = Point(10, 20)
        c = p.x + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        attr_node = find_node(trace_tree, 'p.x')
        assert attr_node is not None
        assert attr_node.value == 10

def test_data_structures():
    def target():
        l = [1, 2]
        t = (3, 4)
        d = {'a': 1}
        s = {5, 6}
        # Trigger exception
        res = l[0] + t[0] + d['a'] + list(s)[0] + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        # We can't easily verify the literal constructions because they are statements in previous lines.
        # But we can verify the access.
        # Wait, the test should verify visit_List, visit_Tuple etc.
        # So we need to construct them in the expression that raises exception.
        pass

def test_data_structures_inline():
    def target():
        # Construct structures inline
        # We use len() to ensure valid operations and trace construction
        res = len([1, 2]) + len((3, 4)) + len({'a': 1}) + len({5, 6}) + (1 / 0)

    instrumented_target = run_instrument(target)
    
    try:
        instrumented_target()
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        frame = tb.tb_frame
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        raw_line = linecache.getline(filename, lineno)
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        
        pos = (lineno, lineno, indent, len(line) + indent)
        trace_tree = build_trace_tree(frame, line, pos)
        
        list_node = find_node(trace_tree, '[1, 2]')
        assert list_node is not None
        assert list_node.value == [1, 2]
        
        tuple_node = find_node(trace_tree, '(3, 4)')
        assert tuple_node is not None
        assert tuple_node.value == (3, 4)
        
        dict_node = find_node(trace_tree, "{'a': 1}")
        assert dict_node is not None
        assert dict_node.value == {'a': 1}
        
        set_node = find_node(trace_tree, '{5, 6}')
        assert set_node is not None
        assert set_node.value == {5, 6}
