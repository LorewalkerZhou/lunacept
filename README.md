# Lunacept

Lunacept is an enhanced exception analysis library for Python. It automatically instruments your code to capture and display the values of intermediate expressions when an exception occurs, making debugging significantly easier.

Instead of just telling you *where* an error happened, Lunacept tells you *why* by showing you the runtime values of every part of the failing expression.

## Features

- **Detailed Exception Reports**: See the values of all sub-expressions in the line that caused the exception.
- **Zero-Config Global Hook**: Easily install a global exception hook that instruments the current module and handles exceptions automatically.
- **Decorator Support**: Use `@capture_exceptions` to instrument and monitor specific functions.
- **Thread Support**: Automatically hooks into `threading.excepthook` to catch exceptions in threads.
- **Manual Handling**: Utilities to print or render detailed exception reports for caught exceptions.

## Installation

```bash
pip install lunacept
```

## Usage

### 1. Global Installation (Recommended for Scripts)

Simply import `lunacept` and call `install()` **after defining your functions** (or inside `if __name__ == "__main__":`). This will instrument the functions in your current module and set up the exception hook.

```python
import lunacept

def get_multiplier(x):
    return x * 2

def complex_calculation(a, b):
    return get_multiplier(a) / (b - 5)

if __name__ == "__main__":
    lunacept.install()
    complex_calculation(10, 5)
```

### Example Output

When the above code runs and fails, Lunacept prints:

```text
Frame #1: "demo.py:11" in <module>()
   line 11, cols 4-30

 10 │ if __name__ == "__main__":
 11 │     lunacept.install()
 12 │     complex_calculation(10, 5)

Expr Tree:
   `-- complex_calculation = <function complex_calculation at 0x...>
────────────────────────────────────────────────────────────

Frame #2: "demo.py:7" in complex_calculation()
   line 7, cols 11-38

  6 │ def complex_calculation(a, b):
  7 │     return get_multiplier(a) / (b - 5)

Expr Tree:
   |-- get_multiplier(a) = 20
   |   |-- get_multiplier = <function get_multiplier at 0x...>
   |   `-- a = 10
   `-- b - 5 = 0
       `-- b = 5
────────────────────────────────────────────────────────────

   ZeroDivisionError: division by zero
```

Notice how it captures that `get_multiplier(a)` returned `20` and `b - 5` evaluated to `0`.



### 2. Decorator Usage

If you want to target specific functions, use the `@capture_exceptions` decorator.

```python
from lunacept import capture_exceptions

@capture_exceptions
def complex_calculation(x, y):
    return (x * 2) / (y - 5)

complex_calculation(10, 5)
```

### 3. Manual Exception Handling

You can also use Lunacept to print details for exceptions you catch yourself.

```python
import lunacept

try:
    val = some_risky_function()
except Exception as e:
    lunacept.print_exception(e)
```

## How It Works

Lunacept uses Python's `ast` (Abstract Syntax Tree) module to parse your code and transform it at runtime. It breaks down complex expressions into a series of temporary variable assignments. 

For example, an expression like:
```python
result = func(a) + b
```
might be internally transformed into something like:
```python
__tmp_1 = func(a)
__tmp_2 = __tmp_1 + b
result = __tmp_2
```
This allows Lunacept to track the value of `func(a)` and `b` individually. When an exception occurs, it uses these captured values to generate a detailed report.

## Performance

Lunacept is designed to be lightweight, but since it instruments code at runtime, there is some overhead. Below are benchmark results comparing standard execution vs. Lunacept instrumentation (MacBook Pro, Apple M1, 16GB RAM):

| Test Case | Baseline | Instrumented | Slowdown |
| :--- | :--- | :--- | :--- |
| **Simple Math** (Arithmetic Loop) | 0.052 ms | 0.068 ms | **1.3x** |
| **Recursive Fib** (Function Calls) | 0.062 ms | 0.089 ms | **1.4x** |
| **Complex Logic** (Branching) | 0.049 ms | 0.056 ms | **1.1x** |

The overhead is generally between **1.1x and 1.4x**, making it suitable for development and testing environments.

## License

This project is licensed under the MIT License.
