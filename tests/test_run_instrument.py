import ast
import inspect
import textwrap
import types
import sys

import lunacept
from lunacept.instrumentor import run_instrument

def test_returns_new_function():
    def f(x):
        return x + 1

    new_f = run_instrument(f)

    assert new_f is not f
    assert isinstance(new_f, types.FunctionType)

    assert new_f.__name__ == f.__name__

    assert new_f(1) == f(1)

def test_exception_line_number():
    def target():
        a = 42
        b = 0
        return a / b

    instrumented = run_instrument(target)

    try:
        instrumented()
    except ZeroDivisionError:
        tb = sys.exc_info()[2]
        # Find the frame for 'target'
        while tb and tb.tb_frame.f_code.co_name != 'target':
            tb = tb.tb_next
            
        assert tb is not None
        
        # The raise statement is 3 lines after the function definition
        # def target():  <- firstlineno
        #     a = 42
        #     b = 0
        #     return a / b  <- firstlineno + 3
        expected_line = target.__code__.co_firstlineno + 3
        assert tb.tb_lineno == expected_line

def test_exception_column_number():
    def target():
        a = 1
        b = 0
        return 100 + (a / b)

    instrumented = run_instrument(target)

    try:
        instrumented()
    except ZeroDivisionError:
        tb = sys.exc_info()[2]
        while tb and tb.tb_frame.f_code.co_name != 'target':
            tb = tb.tb_next
        
        assert tb is not None
        
        lasti = tb.tb_lasti
        code = tb.tb_frame.f_code
            
        positions = list(code.co_positions())
        idx = lasti // 2
        
        if idx < len(positions):
            lineno, end_lineno, col_offset, end_col_offset = positions[idx]
            
            # Find expected column from source
            lines, start_lineno = inspect.getsourcelines(target)
            target_line = None
            for line in lines:
                if "a / b" in line:
                    target_line = line
                    break
            
            assert target_line is not None
            expected_col = target_line.find("a / b")
            
            assert col_offset is not None
            assert col_offset == expected_col


def test_raise_column_number():
    def target():
        a = 1
        b = 0
        raise ValueError(a + b)

    instrumented = run_instrument(target)

    try:
        instrumented()
    except ValueError:
        tb = sys.exc_info()[2]
        while tb and tb.tb_frame.f_code.co_name != 'target':
            tb = tb.tb_next

        assert tb is not None

        lasti = tb.tb_lasti
        code = tb.tb_frame.f_code

        positions = list(code.co_positions())
        idx = lasti // 2

        if idx < len(positions):
            lineno, end_lineno, col_offset, end_col_offset = positions[idx]

            # Find expected column from source
            lines, start_lineno = inspect.getsourcelines(target)
            target_line = None
            for line in lines:
                if "raise ValueError(a + b)" in line:
                    target_line = line
                    break

            assert target_line is not None
            expected_col = target_line.find("raise")

            assert col_offset is not None
            assert col_offset == expected_col

def test_ast_modification():
    def target(x):
        return x * 2

    instrumented = run_instrument(target)
    
    # The instrumentor wraps expressions in NamedExpr with temporary variables
    # starting with __luna_tmp_
    # x * 2 should be wrapped
    assert any(name.startswith("__luna_tmp_") for name in instrumented.__code__.co_varnames)
    assert instrumented(5) == 10

GLOBAL_VALUE = 999
def test_globals_access():
    def target():
        return GLOBAL_VALUE

    instrumented = run_instrument(target)
    assert instrumented() == 999


