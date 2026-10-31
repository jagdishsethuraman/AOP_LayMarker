"""Tests for Seam Mitering & Contract Validation."""

import unittest
from src.core.seam_contracts import SeamContract


class TestSeamValidator(unittest.TestCase):
    def test_perfect_phase_lock(self):
        contract = SeamContract(
            id="cf_placket",
            name="CF Placket Match",
            contract_type="CF_PLACKET",
            piece_a_id="fl",
            piece_b_id="fr",
            description="Placket check match",
            expected_delta_uv=(0.0, 0.0),
            tolerance_mm=1.0,
        )

        # Both placed at valid lattice phases (phase_a = phase_b)
        pos_a = (100.0, 300.0)  # phase (0, 0) on 100x100
        pos_b = (500.0, 700.0)  # phase (0, 0) on 100x100
        res = contract.evaluate(pos_a, pos_b, 100.0, 100.0)
        self.assertTrue(res["passed"])
        self.assertEqual(res["mismatch_mm"], 0.0)

    def test_mismatch_detection(self):
        contract = SeamContract(
            id="cf_placket",
            name="CF Placket Match",
            contract_type="CF_PLACKET",
            piece_a_id="fl",
            piece_b_id="fr",
            description="Placket check match",
            expected_delta_uv=(0.0, 0.0),
            tolerance_mm=1.0,
        )

        # Piece B shifted by 15mm in Y
        pos_a = (100.0, 300.0)
        pos_b = (500.0, 715.0)  # phase (0, 15)
        res = contract.evaluate(pos_a, pos_b, 100.0, 100.0)
        self.assertFalse(res["passed"])
        self.assertAlmostEqual(res["mismatch_mm"], 15.0, places=3)


if __name__ == "__main__":
    unittest.main()
