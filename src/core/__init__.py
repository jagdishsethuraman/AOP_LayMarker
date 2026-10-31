"""Core geometry, lattice, piece models, and seam contracts."""

from .geometry import (
    Point,
    Polygon,
    BBox,
    polygon_bounds,
    polygon_area,
    translate_polygon,
    rotate_polygon,
    polygons_intersect,
    offset_polygon,
    bboxes_intersect,
)
from .repeat_lattice import (
    get_phase,
    phase_error,
    snap_to_lattice,
    get_valid_x_slots,
    get_y_candidate_generator,
)
from .pieces import GarmentPiece, MatchNotch
from .seam_contracts import SeamContract

__all__ = [
    "Point",
    "Polygon",
    "BBox",
    "polygon_bounds",
    "polygon_area",
    "translate_polygon",
    "rotate_polygon",
    "polygons_intersect",
    "offset_polygon",
    "bboxes_intersect",
    "get_phase",
    "phase_error",
    "snap_to_lattice",
    "get_valid_x_slots",
    "get_y_candidate_generator",
    "GarmentPiece",
    "MatchNotch",
    "SeamContract",
]
