"""Garment Pattern Piece Model with Embedded Design Texture Phase."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
from .geometry import (
    Polygon,
    Point,
    BBox,
    polygon_bounds,
    polygon_area,
    translate_polygon,
    rotate_polygon,
    offset_polygon,
)


@dataclass
class MatchNotch:
    """A pattern alignment notch on a seam."""
    id: str
    name: str
    position: Point  # Local (x, y) coordinates relative to piece origin
    seam_edge: str   # e.g., 'CF', 'ARMHOLE', 'SIDE', 'SHOULDER', 'YOKE'


@dataclass
class GarmentPiece:
    """Represents a 2D garment pattern piece with design texture phase constraints."""
    id: str
    name: str
    category: str
    raw_vertices: Polygon
    design_phase: Tuple[float, float]  # (target_u, target_v) in mm
    allowed_rotations: List[float] = field(default_factory=lambda: [0.0])
    seam_allowance_mm: float = 10.0
    buffer_margin_mm: float = 4.0
    color_tag: str = "#38bdf8"
    match_notches: List[MatchNotch] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Cached geometry
    _buffered_cache: Dict[float, Polygon] = field(default_factory=dict, repr=False)

    @property
    def area(self) -> float:
        """Shoelace area in mm²."""
        return abs(polygon_area(self.raw_vertices))

    @property
    def base_bounds(self) -> BBox:
        """Bounding box of unrotated, unplaced raw vertices."""
        return polygon_bounds(self.raw_vertices)

    @property
    def width(self) -> float:
        b = self.base_bounds
        return b[2] - b[0]

    @property
    def height(self) -> float:
        b = self.base_bounds
        return b[3] - b[1]

    def get_placed_polygon(self, x: float, y: float, rotation: float = 0.0) -> Polygon:
        """Return piece vertices translated to (x, y) with rotation."""
        poly = self.raw_vertices
        if rotation != 0.0:
            poly = rotate_polygon(poly, rotation)
        return translate_polygon(poly, x, y)

    def get_buffered_polygon(
        self,
        x: float,
        y: float,
        rotation: float = 0.0,
        buffer_mm: Optional[float] = None,
    ) -> Polygon:
        """Return clearance-buffered polygon translated to (x, y) with rotation."""
        buf = self.buffer_margin_mm if buffer_mm is None else buffer_mm
        if rotation not in self._buffered_cache:
            base_poly = self.raw_vertices
            if rotation != 0.0:
                base_poly = rotate_polygon(base_poly, rotation)
            self._buffered_cache[rotation] = offset_polygon(base_poly, buf)
        buffered = self._buffered_cache[rotation]
        return translate_polygon(buffered, x, y)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize piece for JSON API transfer to frontend."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "vertices": self.raw_vertices,
            "design_phase": {
                "u": self.design_phase[0],
                "v": self.design_phase[1],
            },
            "allowed_rotations": self.allowed_rotations,
            "seam_allowance_mm": self.seam_allowance_mm,
            "buffer_margin_mm": self.buffer_margin_mm,
            "color_tag": self.color_tag,
            "bounds": list(self.base_bounds),
            "area_sq_cm": round(self.area / 100.0, 1),
            "notches": [
                {
                    "id": n.id,
                    "name": n.name,
                    "x": n.position[0],
                    "y": n.position[1],
                    "seam_edge": n.seam_edge,
                }
                for n in self.match_notches
            ],
            "metadata": self.metadata,
        }
