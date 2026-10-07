def hanoi_rec(n, src, dst, aux, moves):
    if n == 0:
        return
    hanoi_rec(n - 1, src, aux, dst, moves)
    moves.append((src, dst))
    hanoi_rec(n - 1, aux, dst, src, moves)


def solve_recursive(n, src="A", dst="C", aux="B"):
    moves = []
    hanoi_rec(n, src, dst, aux, moves)
    return moves


def solve_stack(n, src="A", dst="C", aux="B"):
    """Iterative Towers of Hanoi by emulating the recursion with an explicit stack."""
    moves = []
    stack = [(n, src, dst, aux, 0)]
    while stack:
        n, src, dst, aux, phase = stack.pop()
        if n == 0:
            continue
        if phase == 0:
            stack.append((n, src, dst, aux, 1))
            stack.append((n - 1, src, aux, dst, 0))
        else:
            moves.append((src, dst))
            stack.append((n - 1, aux, dst, src, 0))
    return moves


def solve_iterative(n, src="A", dst="C", aux="B"):
    """Classic no-recursion Hanoi: the smallest disc cycles, the other two pegs do the legal move."""
    moves = []
    pegs = {src: list(range(n, 0, -1)), dst: [], aux: []}
    if n % 2 == 0:
        cycle = {src: aux, aux: dst, dst: src}
    else:
        cycle = {src: dst, dst: aux, aux: src}
    smallest = src
    for step in range(1, 2 ** n):
        if step % 2 == 1:
            a, b = smallest, cycle[smallest]
        else:
            a, b = (p for p in (src, dst, aux) if p != smallest)
            if pegs[a] and (not pegs[b] or pegs[a][-1] < pegs[b][-1]):
                pass
            else:
                a, b = b, a
        pegs[b].append(pegs[a].pop())
        moves.append((a, b))
        if step % 2 == 1:
            smallest = b
    return moves


def fmt(moves):
    return " -> ".join(f"{a}->{b}" for a, b in moves)


def check(n):
    rec = solve_recursive(n)
    stk = solve_stack(n)
    itr = solve_iterative(n)
    ok = rec == stk == itr and len(rec) == 2 ** n - 1
    return rec, stk, itr, ok


def main():
    for n in (3, 4):
        rec, stk, itr, ok = check(n)
        print(f"=== Hanoi n = {n} (moves = {len(rec)}, expected 2^{n}-1 = {2 ** n - 1}) ===")
        print("  recursive  :", fmt(rec))
        print("  stack      :", fmt(stk))
        print("  iterative  :", fmt(itr))
        print("  all identical & count OK:", ok)
        print()


if __name__ == "__main__":
    main()