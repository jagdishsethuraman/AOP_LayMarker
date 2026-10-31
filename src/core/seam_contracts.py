"""Seam Matching & Mitering Contracts.

Defines alignment rules between garment pieces to ensure physical
continuity across seams when cut and stitched.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from .repeat_lattice import get_phase, phase_error


@dataclass
class SeamContract:
    """Contract specifying how two garment pieces must align at a seam."""
    id: str
    name: str
    contract_type: str  # 'CF_PLACKET', 'POCKET_MATCH', 'YOKE_CHEVRON', 'SIDE_SEAM', 'SLEEVE_CHEST'
    piece_a_id: str
    piece_b_id: str
    description: str
    # Expected relative phase difference between piece A and piece B
    expected_delta_uv: Tuple[float, float] = (0.0, 0.0)
    tolerance_mm: float = 1.0

    def evaluate(
        self,
        pos_a: Tuple[float, float],
        pos_b: Tuple[float, float],
        w_rep: float,
        h_rep: float,
    ) -> Dict[str, Any]:
        """Evaluate alignment between pieces placed at pos_a and pos_b on the lay table."""
        phase_a = get_phase(pos_a[0], pos_a[1], w_rep, h_rep)
        phase_b = get_phase(pos_b[0], pos_b[1], w_rep, h_rep)

        # Actual observed phase delta
        actual_du = (phase_a[0] - phase_b[0]) % w_rep
        actual_dv = (phase_a[1] - phase_b[1]) % h_rep

        target_du = self.expected_delta_uv[0] % w_rep
        target_dv = self.expected_delta_uv[1] % h_rep

        err_u = abs(actual_du - target_du)
        err_u = min(err_u, w_rep - err_u)
        err_v = abs(actual_dv - target_dv)
        err_v = min(err_v, h_rep - err_v)

        mismatch_mm = round((err_u**2 + err_v**2) ** 0.5, 3)
        passed = mismatch_mm <= self.tolerance_mm

        return {
            "contract_id": self.id,
            "name": self.name,
            "type": self.contract_type,
            "piece_a": self.piece_a_id,
            "piece_b": self.piece_b_id,
            "phase_a": phase_a,
            "phase_b": phase_b,
            "mismatch_mm": mismatch_mm,
            "passed": passed,
            "tolerance_mm": self.tolerance_mm,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "contract_type": self.contract_type,
            "piece_a_id": self.piece_a_id,
            "piece_b_id": self.piece_b_id,
            "description": self.description,
            "expected_delta_uv": self.expected_delta_uv,
            "tolerance_mm": self.tolerance_mm,
        }
