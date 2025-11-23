import timeit
import lunacept
import sys

# --- Test Functions ---

def simple_math(n):
    """Basic arithmetic operations"""
    res = 0
    for i in range(n):
        res += (i * 2 + 5) / 3
    return res

def recursive_fib(n):
    """Function calls and recursion"""
    if n <= 1:
        return n
    return recursive_fib(n-1) + recursive_fib(n-2)



def complex_logic(n):
    """Mixed logic with branches"""
    res = 0
    for i in range(n):
        if i % 3 == 0:
            res += i
        elif i % 3 == 1:
            res -= i
        else:
            res *= 1.001
    return res

# --- Benchmarking ---

def run_benchmark(label, func, *args, iterations=1000):
    # Warmup
    func(*args)
    
    start_time = timeit.default_timer()
    for _ in range(iterations):
        func(*args)
    end_time = timeit.default_timer()
    
    avg_time = (end_time - start_time) / iterations
    # print(f"{label:<20} | {avg_time*1000:.4f} ms/iter")
    return avg_time

def main():
    print("Running Benchmarks...\n")
    
    # Parameters
    N_MATH = 1000
    N_FIB = 15
    N_LIST = 1000
    N_LOGIC = 1000
    ITERATIONS = 100

    # 1. Baseline (Original functions)
    t1_base = run_benchmark("Simple Math", simple_math, N_MATH, iterations=ITERATIONS)
    t2_base = run_benchmark("Recursive Fib", recursive_fib, N_FIB, iterations=ITERATIONS)
    t4_base = run_benchmark("Complex Logic", complex_logic, N_LOGIC, iterations=ITERATIONS)

    # 2. Instrument
    lunacept.install()
    
    # 3. Instrumented
    t1_inst = run_benchmark("Simple Math", simple_math, N_MATH, iterations=ITERATIONS)
    t2_inst = run_benchmark("Recursive Fib", recursive_fib, N_FIB, iterations=ITERATIONS)
    t4_inst = run_benchmark("Complex Logic", complex_logic, N_LOGIC, iterations=ITERATIONS)

    # 4. Comparison
    print(f"{'Test Case':<20} | {'Baseline':<10} | {'Instrumented':<12} | {'Slowdown':<10}")
    print("-" * 60)
    
    def print_row(name, base, inst):
        ratio = inst / base if base > 0 else 0
        print(f"{name:<20} | {base*1000:.3f} ms   | {inst*1000:.3f} ms     | {ratio:.1f}x")

    print_row("Simple Math", t1_base, t1_inst)
    print_row("Recursive Fib", t2_base, t2_inst)
    print_row("Complex Logic", t4_base, t4_inst)

if __name__ == "__main__":
    main()
