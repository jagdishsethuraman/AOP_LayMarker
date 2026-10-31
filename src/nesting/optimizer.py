"""Sequence Optimizer for Phase-Locked Nesting.

Explores piece placement order permutations via 2-Opt local search
to maximize fabric yield and minimize marker length.
"""

from __future__ import annotations
import random
import time
from typing import List, Optional
from ..core.pieces import GarmentPiece
from .lattice_placer import LatticePlacer, MarkerResult


class NestingOptimizer:
    """Explores piece placement sequences to find optimal marker layouts."""

    def __init__(self, placer: LatticePlacer):
        self.placer = placer

    def optimize(
        self,
        pieces: List[GarmentPiece],
        max_iterations: int = 15,
        time_limit_sec: float = 2.0,
    ) -> MarkerResult:
        """Run 2-Opt sequence search to minimize marker length."""
        t_start = time.perf_counter()

        # Baseline: Priority-first heuristic placement
        best_result = self.placer.place_pieces(pieces, priority_first=True)
        best_length = best_result.marker_length_mm
        best_order = [p.piece for p in best_result.placed_pieces]

        # 2-Opt pairwise perturbation
        n = len(pieces)
        if n <= 2:
            return best_result

        iterations = 0
        while iterations < max_iterations and (time.perf_counter() - t_start) < time_limit_sec:
            iterations += 1
            # Pick two random indices and swap
            i = random.randint(0, n - 2)
            j = random.randint(i + 1, n - 1)

            # Avoid moving the largest core panel below small trims
            cand_order = list(best_order)
            cand_order[i], cand_order[j] = cand_order[j], cand_order[i]

            try:
                cand_result = self.placer.place_pieces(cand_order, priority_first=False)
                if cand_result.marker_length_mm < best_length:
                    best_length = cand_result.marker_length_mm
                    best_result = cand_result
                    best_order = cand_order
            except Exception:
                continue

        best_result.solve_duration_ms = (time.perf_counter() - t_start) * 1000.0
        return best_result
