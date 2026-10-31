"""Phase-Locked Discrete Lattice Engine.

Quantizes 2D marker placement space to ensure physical cuts match the
digital design texture phase exactly upon assembly.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Generator


def get_phase(x: float, y: float, w_rep: float, h_rep: float) -> Tuple[float, float]:
    """Return phase coordinate (u, v) normalized to [0, w_rep) x [0, h_rep)."""
    u = x % w_rep
    if u < 0:
        u += w_rep
    v = y % h_rep
    if v < 0:
        v += h_rep
    return (round(u, 4), round(v, 4))


def phase_error(
    x: float,
    y: float,
    target_u: float,
    target_v: float,
    w_rep: float,
    h_rep: float,
) -> float:
    """Calculate Euclidean phase mismatch distance in mm.

    Factors in wrap-around toroidal distance on the repeat tile.
    """
    curr_u, curr_v = get_phase(x, y, w_rep, h_rep)
    du = abs(curr_u - target_u)
    du = min(du, w_rep - du)
    dv = abs(curr_v - target_v)
    dv = min(dv, h_rep - dv)
    return math.hypot(du, dv)


def snap_to_lattice(
    x: float,
    y: float,
    target_u: float,
    target_v: float,
    w_rep: float,
    h_rep: float,
) -> Tuple[float, float]:
    """Snap an arbitrary (x, y) coordinate to the nearest valid phase lattice node."""
    nx = round((x - target_u) / w_rep)
    ny = round((y - target_v) / h_rep)
    snapped_x = target_u + nx * w_rep
    snapped_y = target_v + ny * h_rep
    return (round(snapped_x, 3), round(snapped_y, 3))


def get_valid_x_slots(
    target_u: float,
    min_x_offset: float,
    max_x_offset: float,
    roll_width: float,
    w_rep: float,
    margin_left: float = 0.0,
    margin_right: float = 0.0,
) -> List[float]:
    """Return all valid horizontal placement coordinates X inside roll boundaries.

    Satisfies:
      X = target_u + nx * w_rep
      X + min_x_offset >= margin_left
      X + max_x_offset <= roll_width - margin_right
    """
    min_allowed_x = margin_left - min_x_offset
    max_allowed_x = (roll_width - margin_right) - max_x_offset

    if min_allowed_x > max_allowed_x:
        return []

    # Solve for integer nx range
    n_min = math.ceil((min_allowed_x - target_u) / w_rep)
    n_max = math.floor((max_allowed_x - target_u) / w_rep)

    slots: List[float] = []
    for nx in range(n_min, n_max + 1):
        x = target_u + nx * w_rep
        slots.append(round(x, 3))
    return slots


def get_y_candidate_generator(
    target_v: float,
    min_y_start: float,
    h_rep: float,
) -> Generator[float, None, None]:
    """Yield ascending valid Y lattice coordinates starting from min_y_start."""
    n_start = math.ceil((min_y_start - target_v) / h_rep)
    if n_start < 0:
        n_start = 0
    curr_n = n_start
    while True:
        y = target_v + curr_n * h_rep
        yield round(y, 3)
        curr_n += 1
