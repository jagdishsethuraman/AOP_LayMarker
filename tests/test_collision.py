"""Tests for 2D Polygon Collision and Geometry Engine."""

import unittest
from src.core.geometry import (
    polygon_area,
    polygon_bounds,
    translate_polygon,
    rotate_polygon,
    polygons_intersect,
    point_in_polygon,
)


class TestGeometry(unittest.TestCase):
    def test_shoelace_area(self):
        # 100 x 50 rectangle
        rect = [(0.0, 0.0), (100.0, 0.0), (100.0, 50.0), (0.0, 50.0)]
        self.assertEqual(polygon_area(rect), 5000.0)

    def test_polygon_bounds(self):
        poly = [(10.0, 20.0), (110.0, 20.0), (80.0, 90.0)]
        bounds = polygon_bounds(poly)
        self.assertEqual(bounds, (10.0, 20.0, 110.0, 90.0))

    def test_point_in_polygon(self):
        poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        self.assertTrue(point_in_polygon((50.0, 50.0), poly))
        self.assertFalse(point_in_polygon((150.0, 50.0), poly))

    def test_polygon_collision_disjoint(self):
        p1 = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        p2 = [(200.0, 0.0), (300.0, 0.0), (300.0, 100.0), (200.0, 100.0)]
        self.assertFalse(polygons_intersect(p1, p2, buffer=4.0))

    def test_polygon_collision_overlapping(self):
        p1 = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        p2 = [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)]
        self.assertTrue(polygons_intersect(p1, p2, buffer=0.0))

    def test_polygon_buffer_margin_collision(self):
        # Separated by 2mm, but buffer is 4mm -> should intersect!
        p1 = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
        p2 = [(102.0, 0.0), (200.0, 0.0), (200.0, 100.0), (102.0, 100.0)]
        self.assertTrue(polygons_intersect(p1, p2, buffer=4.0))


if __name__ == "__main__":
    unittest.main()
