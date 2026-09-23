import sys
import threading
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")

# 方法 1：直接用 Python 內建次方運算
def power2n_1(n):
    return 2**n

# 方法 2a：用遞迴（兩次呼叫，複雜度 O(2^n)）
def power2n_2a(n):
    if n == 0:
        return 1
    return power2n_2a(n - 1) + power2n_2a(n - 1)

# 方法 2b：用遞迴（一次呼叫，複雜度 O(n)）
def power2n_2b(n):
    if n == 0:
        return 1
    return 2 * power2n_2b(n - 1)

# 方法 3：用遞迴 + 查表（memoization）
table = {}

def power2n_3(n):
    if n in table:
        return table[n]
    if n == 0:
        table[0] = 1
        return 1
    result = power2n_3(n - 1) + power2n_3(n - 1)
    table[n] = result
    return result


def timed(func, n):
    start = time.perf_counter()
    result = func(n)
    elapsed = time.perf_counter() - start
    return result, elapsed


def run_with_timeout(func, n, timeout=5):
    result = {"value": None}
    error = {"exc": None}

    def target():
        try:
            result["value"] = func(n)
        except RecursionError as e:
            error["exc"] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None, None, True
    if error["exc"] is not None:
        raise error["exc"]
    return result["value"], 0.0, False


def main():
    N = 100
    expected = 2**N
    print(f"n = {N}  (2**n 預期 = {expected})\n")

    # 方法 1、2b、3：直接測 n = 100
    for name, fn in [("方法 1 (2**n)", power2n_1),
                     ("方法 2b (2*power2n(n-1))", power2n_2b),
                     ("方法 3 (遞迴+查表)", power2n_3)]:
        try:
            result, elapsed = timed(fn, N)
            ok = "OK" if result == expected else "MISMATCH"
            print(f"{name}: n={N} -> {result}")
            print(f"  {'正確' if ok == 'OK' else '錯誤'} | 時間 = {elapsed:.6f} 秒\n")
        except RecursionError:
            print(f"{name}: n={N} -> RecursionError (超出遞迴限制)\n")

    # 方法 2a：先測小 n 展示指數成長
    print("方法 2a (power2n(n-1)+power2n(n-1)) 小 n 測試:")
    prev = None
    for n in range(15, 31):
        _, elapsed = timed(power2n_2a, n)
        ratio = f"  (x{elapsed / prev:.2f})" if prev else ""
        print(f"  n={n}: {elapsed:.4f} 秒{ratio}")
        prev = elapsed
        if elapsed > 3:
            print("  -> 已經太慢，停止繼續增加 n")
            break
    print()

    # 方法 2a：n = 100 加 timeout
    result, _, timed_out = run_with_timeout(power2n_2a, N, timeout=5)
    if timed_out:
        print("方法 2a: n=100 -> 不結束（5 秒 timeout，O(2^n) 對 n=100 不可行）")
    else:
        print(f"方法 2a: n=100 -> {result}")


if __name__ == "__main__":
    main()