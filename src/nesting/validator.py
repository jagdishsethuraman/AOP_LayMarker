"""Seam Matching and Marker Validation Engine."""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from ..core.seam_contracts import SeamContract
from .lattice_placer import PlacedPiece, MarkerResult


class SeamValidator:
    """Evaluates pattern matching quality across all defined garment seam contracts."""

    @staticmethod
    def validate_marker(
        placed_pieces: List[PlacedPiece],
        contracts: List[SeamContract],
        repeat_w_mm: float,
        repeat_h_mm: float,
    ) -> Dict[str, Any]:
        """Verify seam matching contracts against placed marker positions."""
        pos_by_id = {p.piece.id: (p.x, p.y) for p in placed_pieces}
        results = []
        all_passed = True
        max_mismatch = 0.0

        for contract in contracts:
            if contract.piece_a_id not in pos_by_id or contract.piece_b_id not in pos_by_id:
                results.append({
                    "contract_id": contract.id,
                    "name": contract.name,
                    "status": "SKIPPED",
                    "reason": "One or both pieces not present on marker",
                    "mismatch_mm": 0.0,
                    "passed": True,
                })
                continue

            pos_a = pos_by_id[contract.piece_a_id]
            pos_b = pos_by_id[contract.piece_b_id]
            eval_res = contract.evaluate(pos_a, pos_b, repeat_w_mm, repeat_h_mm)
            results.append(eval_res)

            if not eval_res["passed"]:
                all_passed = False
            if eval_res["mismatch_mm"] > max_mismatch:
                max_mismatch = eval_res["mismatch_mm"]

        status_badge = "PERFECT_MATCH" if all_passed and max_mismatch == 0.0 else (
            "WITHIN_TOLERANCE" if all_passed else "MISMATCH_DETECTED"
        )

        return {
            "all_passed": all_passed,
            "max_mismatch_mm": round(max_mismatch, 3),
            "status_badge": status_badge,
            "contracts_count": len(contracts),
            "passed_count": sum(1 for r in results if r.get("passed", False)),
            "evaluations": results,
        }
