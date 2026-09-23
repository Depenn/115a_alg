import math

RECURSIVE_LIMIT = 128


def t1_rec(n):
    if n == 1:
        return 1
    return t1_rec(n - 1) + 8


def t2_rec(n):
    if n == 1:
        return 1
    return 2 * t2_rec(n - 1) + 9


def t3_rec(n):
    if n == 1:
        return 1
    return 2 * t3_rec(n // 2) + 1


def t4_rec(n):
    if n == 1:
        return 1
    return t4_rec(n // 2) + 1


def t1_formula(n):
    return 8 * n - 7


def t2_formula(n):
    return 10 * (2 ** (n - 1)) - 9


def t3_formula(n):
    return 2 * n - 1


def t4_formula(n):
    return int(math.log2(n)) + 1


def check(name, rec, formula, ns):
    ok = True
    for n in ns:
        r, f = rec(n), formula(n)
        status = "OK" if r == f else "FAIL"
        if r != f:
            ok = False
        print(f"{name}: n={n:<4} recursive={r:<14} formula={f:<14} {status}")
    return ok


def main():
    powers_of_two = [2 ** k for k in range(0, 8)]

    results = [
        check("R1 T(n)=T(n-1)+8", t1_rec, t1_formula, list(range(1, RECURSIVE_LIMIT))),
        check("R2 T(n)=2T(n-1)+9", t2_rec, t2_formula, list(range(1, 26))),
        check("R3 T(n)=2T(n/2)+1", t3_rec, t3_formula, powers_of_two),
        check("R4 T(n)=T(n/2)+1", t4_rec, t4_formula, powers_of_two),
    ]

    print()
    names = ["R1", "R2", "R3", "R4"]
    for name, ok in zip(names, results):
        print(f"{name}: {'ALL MATCH' if ok else 'MISMATCH'}")

    if all(results):
        print("\nAll exact formulas verified!")
    else:
        print("\nSome formulas do NOT match - check again.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()