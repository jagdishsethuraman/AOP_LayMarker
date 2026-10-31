"""Tests for Pattern Importers (SVG, DXF, JSON)."""

import unittest
from src.core.importers import SVGPatternImporter, DXFPatternImporter, JSONPatternImporter


class TestImporters(unittest.TestCase):
    def test_svg_import(self):
        sample_svg = """<svg width="500" height="500" xmlns="http://www.w3.org/2000/svg">
            <polygon id="pocket_patch" name="Chest Pocket" points="0,0 120,0 120,130 60,150 0,130" />
            <rect id="collar_band" name="Collar Band" x="10" y="200" width="400" height="40" />
        </svg>"""

        pieces = SVGPatternImporter.parse_svg(sample_svg, default_scale_factor=1.0)
        self.assertEqual(len(pieces), 2)
        self.assertEqual(pieces[0].id, "pocket_patch")
        self.assertEqual(pieces[0].category, "pocket")
        self.assertEqual(pieces[1].id, "collar_band")
        self.assertEqual(pieces[1].category, "collar")

    def test_dxf_import(self):
        sample_dxf = """0
SECTION
2
ENTITIES
0
LWPOLYLINE
8
CUT
70
1
10
0.0
20
0.0
10
200.0
20
0.0
10
200.0
20
400.0
10
0.0
20
400.0
0
ENDSEC
0
EOF"""
        pieces = DXFPatternImporter.parse_dxf(sample_dxf, scale_factor=1.0)
        self.assertEqual(len(pieces), 1)
        self.assertEqual(len(pieces[0].raw_vertices), 4)
        self.assertEqual(pieces[0].width, 200.0)
        self.assertEqual(pieces[0].height, 400.0)

    def test_json_import(self):
        sample_json = """{
            "metadata": {"title": "Test Custom Garment"},
            "pieces": [
                {
                    "id": "front_p",
                    "name": "Front Panel",
                    "vertices": [[0,0], [200,0], [200,300], [0,300]],
                    "design_phase": {"u": 10.0, "v": 20.0}
                }
            ],
            "contracts": []
        }"""
        pieces, contracts, meta = JSONPatternImporter.parse_json(sample_json)
        self.assertEqual(len(pieces), 1)
        self.assertEqual(pieces[0].id, "front_p")
        self.assertEqual(pieces[0].design_phase, (10.0, 20.0))
        self.assertEqual(meta.get("title"), "Test Custom Garment")


if __name__ == "__main__":
    unittest.main()
