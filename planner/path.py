"""Army paths on the strategic map.

Costs are the DAT terrain table (plain/desert 1, forest 2, mountains 4,
river 4); sea and every marker (city 20-99, army 200-247, fleet 300-347) block
an army (terrain-move-cost-table-in-dat.md). Moves are 8-way (the game's
metric is Chebyshev). The game walks each click along a straight line and
stops at the first step it cannot afford, so the driver issues a path as
short straight legs and re-reads the army's position after each one.
"""
import heapq

from state.sav import MAP_H, MAP_W, cell, move_cost


def passable_cost(code):
    if code < 2 or code >= 12:
        return None
    return move_cost(code)


def dijkstra(s, start, goal_fn, max_cost=400, blocked=()):
    """Cheapest path from start to the first tile satisfying goal_fn."""
    dist = {start: 0}
    prev = {}
    pq = [(0, start)]
    blocked = set(blocked)
    while pq:
        d, (x, y) = heapq.heappop(pq)
        if d > dist[(x, y)]:
            continue
        if (x, y) != start and goal_fn(x, y):
            path = [(x, y)]
            while path[-1] != start:
                path.append(prev[path[-1]])
            return d, path[::-1]
        if d > max_cost:
            break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx or dy) and 0 <= nx < MAP_W and 0 <= ny < MAP_H and (nx, ny) not in blocked:
                    c = passable_cost(cell(s, nx, ny))
                    if c is None:
                        continue
                    nd = d + c
                    if nd < dist.get((nx, ny), 1 << 30):
                        dist[(nx, ny)] = nd
                        prev[(nx, ny)] = (x, y)
                        heapq.heappush(pq, (nd, (nx, ny)))
    return None, None


def path_to(s, start, goal):
    return dijkstra(s, start, lambda x, y: (x, y) == tuple(goal))


def path_adjacent(s, start, target):
    """Cheapest path to a free tile at Chebyshev 1 from target (a city or army)."""
    tx, ty = target
    return dijkstra(s, start, lambda x, y: max(abs(x - tx), abs(y - ty)) == 1)


def turn_legs(s, path, moves):
    """Split a path into what one turn's moves pay for: returns (tiles reached
    this turn, cost spent). A human army keeps its remaining moves when the next
    step is unaffordable (terrain-move-cost-table-in-dat.md)."""
    spent, reach = 0, [path[0]]
    for t in path[1:]:
        c = passable_cost(cell(s, *t))
        if spent + c > moves:
            break
        spent += c
        reach.append(t)
    return reach, spent


def turns_needed(s, path, moves_per_turn):
    n, i = 0, 0
    while i < len(path) - 1:
        reach, _ = turn_legs(s, path[i:], moves_per_turn)
        if len(reach) == 1:
            return None
        i += len(reach) - 1
        n += 1
    return n
