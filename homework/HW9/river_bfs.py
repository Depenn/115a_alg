"""Problem 2 - Wolf, goat and cabbage river crossing, solved with Breadth-First Search (BFS).

A farmer must take a wolf, a goat and a cabbage across a river.  The boat holds
the farmer plus at most one item.  Left alone (without the farmer):
    * the wolf eats the goat
    * the goat eats the cabbage

State = which bank each of (farmer, wolf, goat, cabbage) is on, 0 = start bank,
1 = goal bank.  There are only 2^4 = 16 states, 10 of them safe.

BFS explores states level by level (by number of crossings), so the first time it
reaches the goal it has used the *minimum* number of crossings.
"""
from collections import deque

NAMES = ("farmer", "wolf", "goat", "cabbage")
START = (0, 0, 0, 0)
GOAL = (1, 1, 1, 1)


def is_safe(state):
    f, w, g, c = state
    if w == g != f:        # wolf with goat, farmer away
        return False
    if g == c != f:        # goat with cabbage, farmer away
        return False
    return True


def moves(state):
    """Yield (passenger, next_state). passenger is None when the farmer goes alone."""
    f = state[0]
    for item in (None, 1, 2, 3):                  # alone, wolf, goat, cabbage
        if item is not None and state[item] != f:
            continue                              # item must be on farmer's bank
        nxt = list(state)
        nxt[0] = 1 - f
        if item is not None:
            nxt[item] = 1 - f
        nxt = tuple(nxt)
        if is_safe(nxt):
            yield (NAMES[item] if item else None), nxt


def bfs(start=START, goal=GOAL):
    """Return (one shortest path as [(passenger, state), ...], states_expanded)."""
    parent = {start: None}
    q = deque([start])
    expanded = 0
    while q:
        s = q.popleft()
        expanded += 1
        if s == goal:
            break
        for who, nxt in moves(s):
            if nxt not in parent:
                parent[nxt] = (s, who)
                q.append(nxt)
    if goal not in parent:
        return None, expanded
    path, s = [], goal
    while parent[s] is not None:
        prev, who = parent[s]
        path.append((who, s))
        s = prev
    path.append((None, start))
    return path[::-1], expanded


def all_shortest(start=START, goal=GOAL):
    """BFS that keeps *every* parent on the same shortest level -> all shortest solutions."""
    dist = {start: 0}
    parents = {start: []}
    q = deque([start])
    while q:
        s = q.popleft()
        for who, nxt in moves(s):
            if nxt not in dist:
                dist[nxt] = dist[s] + 1
                parents[nxt] = [(s, who)]
                q.append(nxt)
            elif dist[nxt] == dist[s] + 1:
                parents[nxt].append((s, who))

    def build(s):
        if s == start:
            return [[(None, start)]]
        return [p + [(who, s)] for prev, who in parents[s] for p in build(prev)]

    return build(goal) if goal in dist else []


def bank_str(state):
    left = [n[0].upper() for n, side in zip(NAMES, state) if side == 0]
    right = [n[0].upper() for n, side in zip(NAMES, state) if side == 1]
    return f"{''.join(left):>4} |~~~~| {''.join(right):<4}"


def describe(path):
    lines = [f"  start          {bank_str(path[0][1])}"]
    for i, (who, s) in enumerate(path[1:], 1):
        direction = "->" if s[0] == 1 else "<-"
        cargo = who if who else "(alone)"
        lines.append(f"  {i}. {direction} {cargo:<9}  {bank_str(s)}")
    return "\n".join(lines)


def main():
    safe = [s for s in ((a, b, c, d) for a in (0, 1) for b in (0, 1)
                        for c in (0, 1) for d in (0, 1)) if is_safe(s)]
    path, expanded = bfs()
    sols = all_shortest()
    print("=== Wolf / goat / cabbage (BFS) ===")
    print(f"safe states: {len(safe)} of 16, states expanded by BFS: {expanded}")
    print(f"minimum crossings: {len(path) - 1}")
    print("(F=farmer W=wolf G=goat C=cabbage; left bank |~~~~| right bank)")
    print(describe(path))
    print(f"\nnumber of different shortest solutions: {len(sols)}")
    for k, sol in enumerate(sols, 1):
        print(f"solution {k}: " + ", ".join((w or "alone") for w, _ in sol[1:]))


if __name__ == "__main__":
    main()
