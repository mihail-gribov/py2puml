#!/usr/bin/env python3
"""
Test file with syntax error for testing note generation
"""

class TestClass:
    """A test class with syntax error"""
    
    def __init__(self):
        self.value = "test"
    
    def method_with_error(self):
        # This line has a syntax error - unclosed string
        error_string = "This string is not closed properly
        return error_string

def valid_function():
    """A valid function"""
    return "This function is valid"
