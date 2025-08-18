#!/usr/bin/env python3
"""
Simple example of using Xcept - Enhanced Exception Analysis Library
"""

import lunacept

def simple_example():
    """Simple division by zero example"""
    a = 42
    b = 0
    result = a / b  # This will trigger an exception

if __name__ == "__main__":
    # Install the exception handler
    lunacept.install()
    simple_example()
