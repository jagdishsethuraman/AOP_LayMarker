"""Tests for Phase-Locked Discrete Lattice Engine."""

import unittest
from src.core.repeat_lattice import (
    get_phase,
    phase_error,
    snap_to_lattice,
    get_valid_x_slots,
)


class TestRepeatLattice(unittest.TestCase):
    def test_get_phase(self):
        # 100mm repeat
        self.assertEqual(get_phase(100.0, 200.0, 100.0, 100.0), (0.0, 0.0))
        self.assertEqual(get_phase(125.0, 250.0, 100.0, 100.0), (25.0, 50.0))
        # Negative wrap-around
        self.assertEqual(get_phase(-10.0, -25.0, 100.0, 100.0), (90.0, 75.0))

    def test_phase_error(self):
        # Exact match
        err = phase_error(125.0, 350.0, 25.0, 50.0, 100.0, 100.0)
        self.assertAlmostEqual(err, 0.0, places=4)

        # 10mm offset in X
        err = phase_error(135.0, 350.0, 25.0, 50.0, 100.0, 100.0)
        self.assertAlmostEqual(err, 10.0, places=4)

    def test_snap_to_lattice(self):
        # Snap (123.0, 245.0) with target phase (25.0, 50.0) on 100x100 repeat
        snapped_x, snapped_y = snap_to_lattice(123.0, 245.0, 25.0, 50.0, 100.0, 100.0)
        self.assertEqual(snapped_x, 125.0)
        self.assertEqual(snapped_y, 250.0)

    def test_valid_x_slots(self):
        # Roll width 1480mm, piece width 300mm (0 to 300), repeat 100mm, target_u = 20mm
        slots = get_valid_x_slots(
            target_u=20.0,
            min_x_offset=0.0,
            max_x_offset=300.0,
            roll_width=1480.0,
            w_rep=100.0,
            margin_left=10.0,
            margin_right=10.0,
        )
        self.assertTrue(len(slots) > 0)
        for s in slots:
            self.assertAlmostEqual(s % 100.0, 20.0, places=3)
            self.assertGreaterEqual(s, 10.0)
            self.assertLessEqual(s + 300.0, 1470.0)


if __name__ == "__main__":
    unittest.main()
