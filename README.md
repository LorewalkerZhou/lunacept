# Lunacept

**Enhanced Exception Analysis Library for Python**

Lunacept provides precise and elegant exception information that reveals exactly what happened when an error occurs.

## 📋 Requirements

- Python 3.11 or above
- No external dependencies (uses only Python standard library)

## 🚀 Quick Start

```python
import lunacept

# Install the enhanced exception handler
lunacept.install()


# Now all exceptions will show detailed information
def example():
    user_data = {"name": "Alice", "age": 30}
    missing_key = "email"
    result = user_data[missing_key]  # KeyError with detailed context

example()
```

## 📊 Output Example

Instead of a standard traceback, Lunacept shows:

```
============================================================
   KeyError: 'email'
============================================================

Frame #1: example.py:10 in example()
   line 10, cols 14-34

   ┌────────────────────────────────────────────────────────────────────────────────┐
   │   9 │     missing_key = "email"                                                │
   │  10 │     result = user_data[missing_key]                                      │
   │  11 │     return result                                                        │
   └────────────────────────────────────────────────────────────────────────────────┘

Variables:
   user_data = {'name': 'Alice', 'age': 30}
   missing_key = 'email'
```

## 🔧 Configuration

```python
import lunacept

# Configure output style
lunacept.configure(colors=True)  # Enable/disable colors
```