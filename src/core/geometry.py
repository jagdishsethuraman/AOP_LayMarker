"""2D Vector and Polygon Geometry Engine for Pattern Nesting.

Supports polygon transformation, bounding boxes, outward offset buffering,
and robust collision detection for curved garment pieces.
"""

from __future__ import annotations
import math
from typing import List, Tuple, Optional, Sequence

Point = Tuple[float, float]
Polygon = List[Point]
BBox = Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y


def polygon_bounds(poly: Polygon) -> BBox:
    """Compute axis-aligned bounding box (min_x, min_y, max_x, max_y)."""
    if not poly:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def bbox_width_height(bbox: BBox) -> Tuple[float, float]:
    """Return (width, height) of bounding box."""
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])


def bboxes_intersect(b1: BBox, b2: BBox, margin: float = 0.0) -> bool:
    """Return True if two bounding boxes intersect (factoring in optional margin)."""
    if b1[2] + margin < b2[0] - margin or b2[2] + margin < b1[0] - margin:
        return False
    if b1[3] + margin < b2[1] - margin or b2[3] + margin < b1[1] - margin:
        return False
    return True


def polygon_area(poly: Polygon) -> float:
    """Compute signed 2D Shoelace area."""
    n = len(poly)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += poly[i][0] * poly[j][1] - poly[j][0] * poly[i][1]
    return 0.5 * area


def translate_polygon(poly: Polygon, dx: float, dy: float) -> Polygon:
    """Translate polygon by (dx, dy)."""
    return [(p[0] + dx, p[1] + dy) for p in poly]


def rotate_polygon(poly: Polygon, angle_deg: float, origin: Point = (0.0, 0.0)) -> Polygon:
    """Rotate polygon by angle_deg around given origin."""
    if angle_deg == 0.0:
        return list(poly)
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    ox, oy = origin
    res: Polygon = []
    for x, y in poly:
        rx = x - ox
        ry = y - oy
        res.append((ox + rx * cos_a - ry * sin_a, oy + rx * sin_a + ry * cos_a))
    return res


def point_in_polygon(point: Point, poly: Polygon) -> bool:
    """Ray-casting algorithm to test point containment in 2D polygon."""
    x, y = point
    inside = False
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
    return inside


def segments_intersect(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
    """Check if line segment p1-p2 strictly intersects line segment q1-q2."""
    def ccw(a: Point, b: Point, c: Point) -> float:
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])

    d1 = ccw(p1, p2, q1)
    d2 = ccw(p1, p2, q2)
    d3 = ccw(q1, q2, p1)
    d4 = ccw(q1, q2, p2)

    if ((d1 > 1e-7 and d2 < -1e-7) or (d1 < -1e-7 and d2 > 1e-7)) and \
       ((d3 > 1e-7 and d4 < -1e-7) or (d3 < -1e-7 and d4 > 1e-7)):
        return True
    return False


def polygons_intersect(p1: Polygon, p2: Polygon, buffer: float = 0.0) -> bool:
    """Robust 2D polygon collision check handling concave and curved contours.

    Returns True if p1 and p2 intersect (factoring in clearance buffer).
    """
    b1 = polygon_bounds(p1)
    b2 = polygon_bounds(p2)
    if not bboxes_intersect(b1, b2, margin=buffer):
        return False

    # If buffer requested, offset p1's vertices or test distance
    # For fast exact checking:
    n1 = len(p1)
    n2 = len(p2)

    # 1. Edge-edge intersection
    for i in range(n1):
        s1_a = p1[i]
        s1_b = p1[(i + 1) % n1]
        for j in range(n2):
            s2_a = p2[j]
            s2_b = p2[(j + 1) % n2]
            if segments_intersect(s1_a, s1_b, s2_a, s2_b):
                return True
            if buffer > 0.0:
                # Segment-to-segment distance check
                if segment_distance(s1_a, s1_b, s2_a, s2_b) < buffer:
                    return True

    # 2. Point containment (one polygon fully inside the other)
    if point_in_polygon(p1[0], p2) or point_in_polygon(p2[0], p1):
        return True

    return False


def point_segment_distance(p: Point, a: Point, b: Point) -> float:
    """Compute Euclidean distance from point p to line segment a-b."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-9:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def segment_distance(a1: Point, a2: Point, b1: Point, b2: Point) -> float:
    """Compute minimum Euclidean distance between two 2D line segments."""
    if segments_intersect(a1, a2, b1, b2):
        return 0.0
    return min(
        point_segment_distance(a1, b1, b2),
        point_segment_distance(a2, b1, b2),
        point_segment_distance(b1, a1, a2),
        point_segment_distance(b2, a1, a2),
    )


def offset_polygon(poly: Polygon, distance: float) -> Polygon:
    """Outward normal offset for clearance buffer around 2D polygon."""
    if distance <= 0.0:
        return list(poly)
    n = len(poly)
    out: Polygon = []
    # Ensure CCW orientation (positive area)
    if polygon_area(poly) < 0:
        poly = list(reversed(poly))

    for i in range(n):
        prev_p = poly[(i - 1 + n) % n]
        curr_p = poly[i]
        next_p = poly[(i + 1) % n]

        # Normal vector 1 (prev -> curr)
        v1_x = curr_p[0] - prev_p[0]
        v1_y = curr_p[1] - prev_p[1]
        l1 = math.hypot(v1_x, v1_y)
        if l1 > 1e-9:
            n1_x, n1_y = -v1_y / l1, v1_x / l1
        else:
            n1_x, n1_y = 0.0, 1.0

        # Normal vector 2 (curr -> next)
        v2_x = next_p[0] - curr_p[0]
        v2_y = next_p[1] - curr_p[1]
        l2 = math.hypot(v2_x, v2_y)
        if l2 > 1e-9:
            n2_x, n2_y = -v2_y / l2, v2_x / l2
        else:
            n2_x, n2_y = 0.0, 1.0

        # Average normal
        miter_x = n1_x + n2_x
        miter_y = n1_y + n2_y
        m_len = math.hypot(miter_x, miter_y)
        if m_len > 1e-9:
            scale = distance / max(0.5, (n1_x * miter_x / m_len + n1_y * miter_y / m_len))
            # clamp miter spikes
            scale = min(scale, distance * 2.5)
            out.append((curr_p[0] + (miter_x / m_len) * scale, curr_p[1] + (miter_y / m_len) * scale))
        else:
            out.append((curr_p[0] + n1_x * distance, curr_p[1] + n1_y * distance))
    return out
