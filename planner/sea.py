"""Fleet paths on the strategic map: the sea counterpart of `path.py`.

A fleet moves only on sea codes 0 (calm, cost 1) and 1 (rough, cost 3) (`docs/rules-digest.md` §8, terrain-move-cost-table-in-dat.md).
Land, cities (20-99), armies (200-247) and fleets (300-347) block it, except the fleet's own start tile. Moves are 8-way
(Chebyshev). As for armies, the game walks each click along a straight line and stops at the first step it cannot afford, so a
path is issued as short legs and the fleet's position is re-read after each one.

The number of moves a fleet has: `30 - (ships - 50)/10` (26 for 90 ships, 28 for 70), minus `troops aboard / 100 / ships + 1` when it
carries an army, -3 with 0 supplies, and `(70 - condition) >> 2` below condition 70.
"""
import heapq

from state.sav import MAP_H, MAP_W, cell

CALM, ROUGH = 0, 1


def sea_cost(code):
    """Cost of entering a tile for a fleet: 1 on calm sea, 3 on rough sea, None where it cannot go."""
    return {CALM: 1, ROUGH: 3}.get(code)


def fleet_moves(ships, condition=100, supplies=1, troops_aboard=0):
    """A fleet's moves for a turn, from the research formula (not yet checked against every case live)."""
    m = 30 - (ships - 50) // 10
    if troops_aboard:
        m -= troops_aboard // 100 // ships + 1
    if supplies <= 0:
        m -= 3
    if condition < 70:
        m -= (70 - condition) >> 2
    return m


def dijkstra(s, start, goal_fn, max_cost=2000, blocked=()):
    """Cheapest sea path from start to the first tile satisfying goal_fn: (cost, [tiles]) or (None, None)."""
    dist, prev, pq, blocked = {start: 0}, {}, [(0, start)], set(blocked)
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
                    c = sea_cost(cell(s, nx, ny))
                    if c is None:
                        continue
                    nd = d + c
                    if nd < dist.get((nx, ny), 1 << 30):
                        dist[(nx, ny)], prev[(nx, ny)] = nd, (x, y)
                        heapq.heappush(pq, (nd, (nx, ny)))
    return None, None


def sea_path(s, start, goal):
    return dijkstra(s, start, lambda x, y: (x, y) == tuple(goal))


def sea_path_adjacent(s, start, target):
    """Cheapest path to a free sea tile at Chebyshev 1 from `target` (another fleet or a city)."""
    tx, ty = target
    return dijkstra(s, start, lambda x, y: max(abs(x - tx), abs(y - ty)) == 1)


def legs(s, path, moves):
    """What `moves` pay for along `path`: (tiles reached this turn, cost spent). The fleet keeps its remaining moves when
    the next step is unaffordable."""
    spent, reach = 0, [path[0]]
    for t in path[1:]:
        c = sea_cost(cell(s, *t))
        if c is None or spent + c > moves:
            break
        spent += c
        reach.append(t)
    return reach, spent


def path_cost(s, path):
    return sum(sea_cost(cell(s, *t)) for t in path[1:])
