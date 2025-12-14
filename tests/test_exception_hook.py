"""
Test the exception_hook module's helper functions.
Specifically testing _get_project_root and _is_module_in_project.
"""
import sys
import os
import tempfile
import types
from pathlib import Path
from lunacept.exception_hook import _get_project_root, _is_module_in_project


def test_get_project_root_from_main_module():
    """
    Test that _get_project_root correctly identifies the project root
    from the __main__ module.
    """
    # Save original __main__ module
    original_main = sys.modules.get('__main__')
    
    try:
        # Create a fake __main__ module with a __file__ attribute
        fake_main = types.ModuleType('__main__')
        fake_main.__file__ = '/fake/project/main.py'
        sys.modules['__main__'] = fake_main
        
        # Get project root
        root = _get_project_root()
        
        # Should return the directory containing main.py
        expected = os.path.dirname(os.path.abspath(fake_main.__file__))
        assert root == expected, f"Expected '{expected}', got '{root}'"
    finally:
        # Restore original __main__ module
        if original_main is not None:
            sys.modules['__main__'] = original_main
        else:
            sys.modules.pop('__main__', None)


def test_get_project_root_without_main_file():
    """
    Test that _get_project_root falls back to caller's file when __main__ has no __file__.
    """
    # Save original __main__ module
    original_main = sys.modules.get('__main__')
    
    try:
        # Create a fake __main__ module without __file__
        fake_main = types.ModuleType('__main__')
        sys.modules['__main__'] = fake_main
        
        # Get project root - should fall back to caller's file (this test file)
        root = _get_project_root()
        
        # The root should be the directory containing this test file
        expected_dir = os.path.dirname(os.path.abspath(__file__))
        assert root == expected_dir, f"Expected {expected_dir}, got {root}"
    finally:
        # Restore original __main__ module
        if original_main is not None:
            sys.modules['__main__'] = original_main
        else:
            sys.modules.pop('__main__', None)


def test_get_project_root_no_main_module():
    """
    Test that _get_project_root falls back to caller's file when __main__ module is missing.
    """
    # Save original __main__ module
    original_main = sys.modules.get('__main__')
    
    try:
        # Remove __main__ module
        if '__main__' in sys.modules:
            del sys.modules['__main__']

        # Get project root - should use fallback to caller's file
        root = _get_project_root()
        
        # The root should be the directory containing this test file
        expected_dir = os.path.dirname(os.path.abspath(__file__))
        assert root == expected_dir, f"Expected {expected_dir}, got {root}"
    finally:
        # Restore original __main__ module
        if original_main is not None:
            sys.modules['__main__'] = original_main


def test_is_module_in_project_user_module():
    """
    Test that _is_module_in_project correctly identifies user modules.
    """
    # Create a fake module that appears to be in the project
    fake_module = types.ModuleType('fake_user_module')
    fake_module.__file__ = '/home/user/myproject/mymodule.py'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is True, "User module should be identified as in project"


def test_is_module_in_project_outside_project():
    """
    Test that _is_module_in_project rejects modules outside project root.
    """
    # Create a fake module outside the project
    fake_module = types.ModuleType('fake_external_module')
    fake_module.__file__ = '/usr/lib/python3/external.py'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "External module should not be identified as in project"


def test_is_module_in_project_site_packages():
    """
    Test that _is_module_in_project excludes site-packages modules.
    """
    # Create a fake module in site-packages
    fake_module = types.ModuleType('fake_third_party')
    fake_module.__file__ = '/home/user/myproject/venv/lib/python3.12/site-packages/package.py'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "site-packages module should be excluded"


def test_is_module_in_project_pycache():
    """
    Test that _is_module_in_project excludes __pycache__ files.
    """
    # Create a fake module in __pycache__
    fake_module = types.ModuleType('fake_cached')
    fake_module.__file__ = '/home/user/myproject/__pycache__/module.cpython-312.pyc'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "__pycache__ files should be excluded"


def test_is_module_in_project_pyc_file():
    """
    Test that _is_module_in_project excludes .pyc files.
    """
    # Create a fake module with .pyc extension
    fake_module = types.ModuleType('fake_compiled')
    fake_module.__file__ = '/home/user/myproject/module.pyc'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, ".pyc files should be excluded"


def test_is_module_in_project_no_file_attribute():
    """
    Test that _is_module_in_project handles modules without __file__.
    """
    # Create a fake module without __file__
    fake_module = types.ModuleType('fake_no_file')
    # Don't set __file__ attribute
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "Module without __file__ should return False"


def test_is_module_in_project_none_file():
    """
    Test that _is_module_in_project handles modules with None __file__.
    """
    # Create a fake module with None __file__
    fake_module = types.ModuleType('fake_none_file')
    fake_module.__file__ = None
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "Module with None __file__ should return False"


def test_is_module_in_project_nested_structure():
    """
    Test that _is_module_in_project works with nested package structures.
    """
    # Create a fake module in a nested package
    fake_module = types.ModuleType('fake_nested')
    fake_module.__file__ = '/home/user/myproject/pkg1/pkg2/module.py'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is True, "Nested package module should be identified as in project"


def test_is_module_in_project_builtin_module():
    """
    Test that _is_module_in_project correctly handles built-in modules.
    """
    import sys as builtin_module
    
    project_root = '/home/user/myproject'
    
    # Built-in modules typically don't have __file__ or have special paths
    result = _is_module_in_project(builtin_module, project_root)
    assert result is False, "Built-in module should not be identified as in project"


def test_is_module_in_project_actual_third_party():
    """
    Test with an actual third-party module if available.
    """
    try:
        import pytest
        project_root = '/home/user/myproject'
        
        result = _is_module_in_project(pytest, project_root)
        assert result is False, "Third-party module (pytest) should not be in project"
    except ImportError:
        # pytest not installed, skip this test
        pass


def test_is_module_in_project_edge_case_similar_paths():
    """
    Test that _is_module_in_project doesn't match similar but different paths.
    """
    # Create a module in a path that starts with project root but isn't inside it
    fake_module = types.ModuleType('fake_similar')
    fake_module.__file__ = '/home/user/myproject_other/module.py'
    
    project_root = '/home/user/myproject'
    
    result = _is_module_in_project(fake_module, project_root)
    assert result is False, "Module in similar path should not be identified as in project"
