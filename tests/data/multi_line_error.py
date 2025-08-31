import lunacept

def multi_line_error():
    a = 42
    b = 0
    result = a /\
             b # multi-line ZeroDivisionError

if __name__ == "__main__":
    lunacept.install()
    multi_line_error()