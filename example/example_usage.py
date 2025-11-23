#!/usr/bin/env python3
"""
Example demonstrating Lunacept's expression tracking capabilities
"""
import lunacept

class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def get_info(self):
        return {"name": self.name, "age": self.age}

def get_user_data():
    return {"name": "Alice", "age": 30}

def example():
    """Demonstrates tracking of nested calls, attribute access, and dictionary operations"""
    user = User("Bob", 25)
    info = user.get_info()
    missing_key = "email"
    result = get_user_data()[missing_key]  # KeyError with detailed context
    return result

if __name__ == "__main__":
    lunacept.install()
    example()
