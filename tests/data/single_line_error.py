import lunacept

def single_line_error():
    a = 42
    b = 0
    result = a / b  # single-line ZeroDivisionError

if __name__ == "__main__":
    lunacept.install()
    single_line_error()