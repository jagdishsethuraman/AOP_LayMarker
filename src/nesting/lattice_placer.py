"""Phase-Locked Bottom-Left-Lattice (BLL) Heuristic Placer.

Restricts piece placement candidates strictly to the discrete repeat lattice,
guaranteeing 100% seam pattern match upon cutting.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from ..core.geometry import (
    Polygon,
    BBox,
    polygon_bounds,
    polygons_intersect,
    bboxes_intersect,
)
from ..core.pieces import GarmentPiece
from ..core.repeat_lattice import get_valid_x_slots, get_phase, phase_error


@dataclass
class PlacedPiece:
    """A garment piece positioned on the cutting lay marker."""
    piece: GarmentPiece
    x: float
    y: float
    rotation: float
    placed_vertices: Polygon
    buffered_vertices: Polygon
    bounds: BBox  # (min_x, min_y, max_x, max_y) on the marker bed

    @property
    def max_y(self) -> float:
        return self.bounds[3]

    @property
    def max_x(self) -> float:
        return self.bounds[2]


@dataclass
class MarkerResult:
    """Result of a nesting solution on the fabric roll."""
    placed_pieces: List[PlacedPiece]
    roll_width_mm: float
    marker_length_mm: float
    repeat_w_mm: float
    repeat_h_mm: float
    buffer_mm: float
    utilization_pct: float
    solve_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roll_width_mm": self.roll_width_mm,
            "marker_length_mm": round(self.marker_length_mm, 1),
            "repeat_w_mm": self.repeat_w_mm,
            "repeat_h_mm": self.repeat_h_mm,
            "buffer_mm": self.buffer_mm,
            "utilization_pct": round(self.utilization_pct, 2),
            "solve_duration_ms": round(self.solve_duration_ms, 1),
            "pieces": [
                {
                    "id": p.piece.id,
                    "name": p.piece.name,
                    "category": p.piece.category,
                    "color_tag": p.piece.color_tag,
                    "x": round(p.x, 2),
                    "y": round(p.y, 2),
                    "rotation": p.rotation,
                    "bounds": [round(b, 2) for b in p.bounds],
                    "placed_vertices": [[round(pt[0], 2), round(pt[1], 2)] for pt in p.placed_vertices],
                    "design_phase": {
                        "u": p.piece.design_phase[0],
                        "v": p.piece.design_phase[1],
                    },
                    "actual_phase": {
                        "u": round(p.x % self.repeat_w_mm, 2),
                        "v": round(p.y % self.repeat_h_mm, 2),
                    },
                    "phase_error_mm": round(
                        phase_error(
                            p.x,
                            p.y,
                            p.piece.design_phase[0],
                            p.piece.design_phase[1],
                            self.repeat_w_mm,
                            self.repeat_h_mm,
                        ),
                        3,
                    ),
                }
                for p in self.placed_pieces
            ],
        }


class LatticePlacer:
    """Bottom-Left-Lattice heuristic placing pieces onto valid repeat phase nodes."""

    def __init__(
        self,
        roll_width_mm: float,
        repeat_w_mm: float,
        repeat_h_mm: float,
        margin_left_mm: float = 10.0,
        margin_right_mm: float = 10.0,
        buffer_mm: float = 4.0,
    ):
        self.roll_width_mm = roll_width_mm
        self.repeat_w_mm = repeat_w_mm
        self.repeat_h_mm = repeat_h_mm
        self.margin_left_mm = margin_left_mm
        self.margin_right_mm = margin_right_mm
        self.buffer_mm = buffer_mm

    def place_pieces(
        self,
        pieces: List[GarmentPiece],
        priority_first: bool = True,
    ) -> MarkerResult:
        """Execute phase-locked placement for the given garment pieces."""
        t_start = time.perf_counter()

        # Sort pieces: large bodies & matched cores first
        def sort_key(p: GarmentPiece):
            # Categories: body/skirt (3), yoke (2), pocket/collar/sleeve (1)
            cat_score = 3 if p.category in ("body", "skirt") else (2 if p.category == "yoke" else 1)
            return (cat_score, p.area)

        ordered = sorted(pieces, key=sort_key, reverse=True) if priority_first else list(pieces)

        placed: List[PlacedPiece] = []

        for piece in ordered:
            best_placement = self._find_best_lattice_slot(piece, placed)
            if best_placement is not None:
                placed.append(best_placement)
            else:
                raise RuntimeError(f"Unable to place piece '{piece.name}' inside roll width {self.roll_width_mm}mm")

        # Compute marker length and fabric yield
        max_y = max((p.max_y for p in placed), default=0.0)
        marker_length = max(max_y + 10.0, 100.0)  # plus end margin

        total_piece_area = sum(p.piece.area for p in placed)
        marker_fabric_area = self.roll_width_mm * marker_length
        utilization = (total_piece_area / marker_fabric_area) * 100.0 if marker_fabric_area > 0 else 0.0

        t_end = time.perf_counter()

        return MarkerResult(
            placed_pieces=placed,
            roll_width_mm=self.roll_width_mm,
            marker_length_mm=marker_length,
            repeat_w_mm=self.repeat_w_mm,
            repeat_h_mm=self.repeat_h_mm,
            buffer_mm=self.buffer_mm,
            utilization_pct=utilization,
            solve_duration_ms=(t_end - t_start) * 1000.0,
        )

    def _find_best_lattice_slot(
        self,
        piece: GarmentPiece,
        already_placed: List[PlacedPiece],
    ) -> Optional[PlacedPiece]:
        """Find the optimal (lowest Y, then lowest X) valid lattice position for piece."""
        best_candidate: Optional[PlacedPiece] = None
        best_score = float("inf")

        for rot in piece.allowed_rotations:
            # Piece bounds at rotation rot
            rot_poly = piece.get_placed_polygon(0.0, 0.0, rotation=rot)
            b = polygon_bounds(rot_poly)
            min_x_off, min_y_off, max_x_off, max_y_off = b

            # Get horizontal lattice slots that keep piece strictly within roll boundaries
            target_u, target_v = piece.design_phase
            x_slots = get_valid_x_slots(
                target_u=target_u,
                min_x_offset=min_x_off,
                max_x_offset=max_x_off,
                roll_width=self.roll_width_mm,
                w_rep=self.repeat_w_mm,
                margin_left=self.margin_left_mm,
                margin_right=self.margin_right_mm,
            )

            if not x_slots:
                continue

            # Minimum starting Y coordinate
            min_allowed_y = 10.0 - min_y_off  # margin_top
            n_start = math.ceil((min_allowed_y - target_v) / self.repeat_h_mm)
            if n_start < 0:
                n_start = 0

            # Scan lattice candidates across X slots
            for x_cand in x_slots:
                ny = n_start
                # Step up through valid repeat periods until non-colliding slot is found
                max_steps = 300
                for _ in range(max_steps):
                    y_cand = target_v + ny * self.repeat_h_mm
                    cand_bounds = (
                        x_cand + min_x_off,
                        y_cand + min_y_off,
                        x_cand + max_x_off,
                        y_cand + max_y_off,
                    )

                    # Collision test against already placed pieces
                    collides = False
                    cand_buf_poly = None

                    for other in already_placed:
                        if bboxes_intersect(cand_bounds, other.bounds, margin=self.buffer_mm):
                            # Bounding boxes overlap, test exact polygon buffer
                            if cand_buf_poly is None:
                                cand_buf_poly = piece.get_buffered_polygon(x_cand, y_cand, rotation=rot, buffer_mm=self.buffer_mm)
                            if polygons_intersect(cand_buf_poly, other.buffered_vertices, buffer=0.0):
                                collides = True
                                break

                    if not collides:
                        # Bottom-Left gravity score: prioritize low Y, then low X
                        score = y_cand + 0.05 * x_cand
                        if score < best_score:
                            best_score = score
                            placed_poly = piece.get_placed_polygon(x_cand, y_cand, rotation=rot)
                            if cand_buf_poly is None:
                                cand_buf_poly = piece.get_buffered_polygon(x_cand, y_cand, rotation=rot, buffer_mm=self.buffer_mm)
                            best_candidate = PlacedPiece(
                                piece=piece,
                                x=x_cand,
                                y=y_cand,
                                rotation=rot,
                                placed_vertices=placed_poly,
                                buffered_vertices=cand_buf_poly,
                                bounds=cand_bounds,
                            )
                        break  # Found lowest valid Y for this X slot
                    ny += 1

        return best_candidate
