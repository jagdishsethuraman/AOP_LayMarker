"""Tests for Phase-Locked Nesting Solver and Compactor."""

import unittest
from src.presets.plaid_shirt import create_plaid_shirt_preset
from src.presets.striped_tee import create_striped_tee_preset
from src.nesting.lattice_placer import LatticePlacer
from src.nesting.optimizer import NestingOptimizer
from src.nesting.validator import SeamValidator


class TestNesting(unittest.TestCase):
    def test_plaid_shirt_nesting(self):
        pieces, contracts, meta = create_plaid_shirt_preset()
        placer = LatticePlacer(
            roll_width_mm=meta["roll_width_mm"],
            repeat_w_mm=meta["repeat_width_mm"],
            repeat_h_mm=meta["repeat_height_mm"],
            buffer_mm=4.0,
        )

        res = placer.place_pieces(pieces, priority_first=True)
        self.assertEqual(len(res.placed_pieces), len(pieces))
        self.assertGreater(res.marker_length_mm, 500.0)
        self.assertGreater(res.utilization_pct, 40.0)

        # Verify all pieces stay strictly within roll width
        for p in res.placed_pieces:
            self.assertGreaterEqual(p.bounds[0], 10.0)
            self.assertLessEqual(p.bounds[2], meta["roll_width_mm"] - 10.0)

        # Verify exact seam matching (mismatch must be 0.00mm)
        val = SeamValidator.validate_marker(
            res.placed_pieces,
            contracts,
            repeat_w_mm=meta["repeat_width_mm"],
            repeat_h_mm=meta["repeat_height_mm"],
        )
        self.assertTrue(val["all_passed"])
        self.assertEqual(val["max_mismatch_mm"], 0.0)

    def test_striped_tee_nesting_and_optimizer(self):
        pieces, contracts, meta = create_striped_tee_preset()
        placer = LatticePlacer(
            roll_width_mm=meta["roll_width_mm"],
            repeat_w_mm=meta["repeat_width_mm"],
            repeat_h_mm=meta["repeat_height_mm"],
            buffer_mm=4.0,
        )

        optimizer = NestingOptimizer(placer)
        opt_res = optimizer.optimize(pieces, max_iterations=6, time_limit_sec=1.0)
        self.assertEqual(len(opt_res.placed_pieces), len(pieces))

        val = SeamValidator.validate_marker(
            opt_res.placed_pieces,
            contracts,
            repeat_w_mm=meta["repeat_width_mm"],
            repeat_h_mm=meta["repeat_height_mm"],
        )
        self.assertTrue(val["all_passed"])
        self.assertEqual(val["max_mismatch_mm"], 0.0)


if __name__ == "__main__":
    unittest.main()
