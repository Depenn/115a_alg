"""Self-made map/filter/reduce and a loop-free bubble sort built on top of them.

No `for` and no `while` anywhere in this file: every function is either
recursive or a composition of my_map / my_filter / my_reduce.
"""

ADD = lambda a, b: a + b
EVEN = lambda x: x % 2 == 0
SQUARE = lambda x: x * x


def head(xs):
    return xs[0]


def tail(xs):
    return xs[1:]


def my_map(f, xs):
    if xs == []:
        return []
    return [f(head(xs))] + my_map(f, tail(xs))


def my_filter(pred, xs):
    if xs == []:
        return []
    x = head(xs)
    if pred(x):
        return [x] + my_filter(pred, tail(xs))
    return my_filter(pred, tail(xs))


def my_reduce(f, xs, init):
    if xs == []:
        return init
    return my_reduce(f, tail(xs), f(init, head(xs)))


def last(xs):
    if tail(xs) == []:
        return head(xs)
    return last(tail(xs))


def init(xs):
    if tail(xs) == []:
        return []
    return [head(xs)] + init(tail(xs))


def sift(acc, x):
    """One bubble-step: if x is smaller than the back of the list, swap it back."""
    if acc == [] or last(acc) <= x:
        return acc + [x]
    return init(acc) + [x, last(acc)]


def bubble_pass(xs):
    """One sweep of bubble sort: the largest element bubbles to the right end."""
    return my_reduce(sift, xs, [])


def bubble_sort(xs):
    if tail(xs) == []:
        return xs
    passed = bubble_pass(xs)
    return bubble_sort(init(passed)) + [last(passed)]


def pairs(xs):
    if tail(xs) == []:
        return []
    return [(head(xs), head(tail(xs)))] + pairs(tail(xs))


def is_sorted(xs):
    return my_reduce(lambda ok, p: ok and p[0] <= p[1], pairs(xs), True)


def equal_lists(a, b):
    if a == [] and b == []:
        return True
    if a == [] or b == []:
        return False
    if head(a) != head(b):
        return False
    return equal_lists(tail(a), tail(b))


def same_as_builtin(xs):
    return equal_lists(bubble_sort(xs), sorted(xs))


def show_tests(tests):
    if tests == []:
        return
    t = head(tests)
    r = bubble_sort(t)
    print(f"  bubble_sort({str(t):<22}) = {r}   ok = {is_sorted(r) and same_as_builtin(t)}")
    show_tests(tail(tests))


def main():
    arr = [3, 5, 2, 4, 1]
    print("=== self-made map / filter / reduce (all recursive, no loops) ===")
    print(f"  my_map(SQUARE, {arr})     = {my_map(SQUARE, arr)}")
    print(f"  my_filter(EVEN, {arr})   = {my_filter(EVEN, arr)}")
    print(f"  my_reduce(ADD, {arr}, 0)  = {my_reduce(ADD, arr, 0)}")
    print()

    print("=== bubble sort, loop-free, built only on my_reduce + recursion ===")
    print(f"  one bubble_pass {arr}  = {bubble_pass(arr)}   (largest -> right end)")
    print(f"  bubble_sort     {arr}  = {bubble_sort(arr)}")
    print(f"  is_sorted(result)          = {is_sorted(bubble_sort(arr))}")
    print(f"  equal to built-in sorted() = {same_as_builtin(arr)}")
    print()

    tests = [[], [1], [3, 1, 2], [3, 3, 1, 2, 2], [9, 5, 7, 1, 8, 3]]
    print("=== extra cases ===")
    show_tests(tests)


if __name__ == "__main__":
    main()