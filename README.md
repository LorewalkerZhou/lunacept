# Lunacept

Lunacept is an enhanced exception analysis library for Python. It automatically instruments your code to capture and display the values of intermediate expressions when an exception occurs, making debugging significantly easier.

Instead of just telling you *where* an error happened, Lunacept tells you *why* by showing you the runtime values of every part of the failing expression.

![Lunacept Example](docs/images/example.png)

## Highlights

* Show the values of all sub-expressions at the exact position (line and column) that caused the exception. 

* Easy to use - no need to modify your existing code. 

* Low Overhead, benchmark results show overhead between 1.1x and 1.4x:


## Installation

```bash
pip install lunacept
```

## Usage

Simply import `lunacept` and call `install()`:

```python
import lunacept

def main():
    # Your existing code - no changes needed

if __name__ == "__main__":
    lunacept.install()
    main()
```

You can also use the `@capture_exceptions` decorator to instrument specific functions:

```python
from lunacept import capture_exceptions

@capture_exceptions
def your_function():
    ...
```

## How It Works

Lunacept uses Python's `ast` (Abstract Syntax Tree) module to parse and transform your code at runtime. It breaks down complex expressions into temporary variable assignments, allowing it to track the value of each sub-expression individually. When an exception occurs, Lunacept uses these captured values to generate a detailed report.

## Performance

Lunacept is designed to be lightweight, but since it instruments code at runtime, there is some overhead. Below are benchmark results comparing standard execution vs. Lunacept instrumentation (MacBook Pro, Apple M1, 16GB RAM):

| Test Case | Baseline | Instrumented | Slowdown |
| :--- | :--- | :--- | :--- |
| **Simple Math** (Arithmetic Loop) | 0.052 ms | 0.068 ms | **1.3x** |
| **Recursive Fib** (Function Calls) | 0.062 ms | 0.089 ms | **1.4x** |
| **Complex Logic** (Branching) | 0.049 ms | 0.056 ms | **1.1x** |

The overhead is generally between **1.1x and 1.4x**

## License

This project is licensed under the MIT License.
