"""Garment Pattern Importers for SVG, DXF, and Custom JSON.

Provides zero-dependency parsers to import 2D garment patterns from
apparel CAD systems (CLO 3D, Browzwear, Gerber, Lectra, Illustrator).
"""

from __future__ import annotations
import math
import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
from .pieces import GarmentPiece, MatchNotch
from .geometry import Polygon, Point, polygon_bounds


class SVGPatternImporter:
    """Extracts 2D garment pattern pieces from SVG cut patterns."""

    @staticmethod
    def parse_svg(
        svg_content: str,
        default_scale_factor: float = 1.0,  # 1.0 for mm, 0.264583 for 96dpi px -> mm
    ) -> List[GarmentPiece]:
        """Parse SVG paths, polygons, and rects into GarmentPiece objects."""
        # Strip namespaces for easier XPath querying
        clean_xml = re.sub(r'\sxmlns(:\w+)?="[^"]+"', '', svg_content, count=1)
        root = ET.fromstring(clean_xml)

        pieces: List[GarmentPiece] = []
        piece_idx = 1

        # Search for path, polygon, rect elements
        for elem in root.iter():
            tag = elem.tag.lower().split('}')[-1]
            verts: Optional[Polygon] = None
            elem_id = elem.attrib.get('id', f'piece_{piece_idx}')
            elem_name = elem.attrib.get('name', elem.attrib.get('title', elem_id))

            if tag == 'polygon':
                pts_str = elem.attrib.get('points', '')
                verts = SVGPatternImporter._parse_points_str(pts_str, default_scale_factor)

            elif tag == 'rect':
                try:
                    x = float(elem.attrib.get('x', 0.0)) * default_scale_factor
                    y = float(elem.attrib.get('y', 0.0)) * default_scale_factor
                    w = float(elem.attrib.get('width', 0.0)) * default_scale_factor
                    h = float(elem.attrib.get('height', 0.0)) * default_scale_factor
                    if w > 10 and h > 10:
                        verts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                except ValueError:
                    pass

            elif tag == 'path':
                d_str = elem.attrib.get('d', '')
                verts = SVGPatternImporter._approximate_path_polygon(d_str, default_scale_factor)

            if verts and len(verts) >= 3:
                # Normalize piece origin to (0, 0)
                bounds = polygon_bounds(verts)
                min_x, min_y = bounds[0], bounds[1]
                norm_verts = [(round(p[0] - min_x, 2), round(p[1] - min_y, 2)) for p in verts]

                # Assign categorical guessing
                category = "body"
                name_lower = elem_name.lower()
                if "pocket" in name_lower:
                    category = "pocket"
                elif "yoke" in name_lower:
                    category = "yoke"
                elif "sleeve" in name_lower:
                    category = "sleeve"
                elif "collar" in name_lower:
                    category = "collar"
                elif "cuff" in name_lower or "band" in name_lower:
                    category = "trim"

                piece = GarmentPiece(
                    id=elem_id.replace(" ", "_"),
                    name=elem_name,
                    category=category,
                    raw_vertices=norm_verts,
                    design_phase=(0.0, 0.0),  # Default phase; user can link in UI
                    allowed_rotations=[0.0],
                    color_tag=SVGPatternImporter._pick_color(piece_idx),
                )
                pieces.append(piece)
                piece_idx += 1

        return pieces

    @staticmethod
    def _parse_points_str(pts_str: str, scale: float) -> Polygon:
        pts = []
        raw_coords = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', pts_str)
        for i in range(0, len(raw_coords) - 1, 2):
            pts.append((float(raw_coords[i]) * scale, float(raw_coords[i + 1]) * scale))
        return pts

    @staticmethod
    def _approximate_path_polygon(d_str: str, scale: float) -> Optional[Polygon]:
        """Convert SVG path line/moveto commands into a discrete 2D polygon."""
        points: Polygon = []
        curr_x, curr_y = 0.0, 0.0

        # Tokenize SVG path commands
        commands = re.findall(r'([A-Za-z])|([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)', d_str)
        curr_cmd = 'M'
        coord_buffer: List[float] = []

        for cmd, val in commands:
            if cmd:
                curr_cmd = cmd
                coord_buffer = []
            elif val:
                coord_buffer.append(float(val))
                if curr_cmd.upper() in ('M', 'L') and len(coord_buffer) >= 2:
                    if curr_cmd == 'M' or curr_cmd == 'L':
                        curr_x, curr_y = coord_buffer[0] * scale, coord_buffer[1] * scale
                    elif curr_cmd == 'm' or curr_cmd == 'l':
                        curr_x += coord_buffer[0] * scale
                        curr_y += coord_buffer[1] * scale
                    points.append((round(curr_x, 2), round(curr_y, 2)))
                    coord_buffer = []

        return points if len(points) >= 3 else None

    @staticmethod
    def _pick_color(idx: int) -> str:
        colors = ["#38bdf8", "#818cf8", "#e5a93c", "#34d399", "#f472b6", "#a78bfa", "#f59e0b", "#10b981"]
        return colors[(idx - 1) % len(colors)]


class DXFPatternImporter:
    """Lightweight zero-dependency ASCII DXF parser for AAMA/ASTM apparel cut patterns."""

    @staticmethod
    def parse_dxf(dxf_content: str, scale_factor: float = 1.0) -> List[GarmentPiece]:
        """Extract closed polylines on cutting layers (e.g. 1, CUT, OUTLINE)."""
        lines = dxf_content.splitlines()
        pieces: List[GarmentPiece] = []
        piece_idx = 1

        i = 0
        n = len(lines)
        curr_entity: Optional[str] = None
        curr_layer: str = "0"
        curr_points: List[Point] = []
        is_closed = False

        while i < n - 1:
            code = lines[i].strip()
            val = lines[i + 1].strip()
            i += 2

            if code == "0":
                # Process previous entity if it was a polyline
                if curr_entity in ("LWPOLYLINE", "POLYLINE") and len(curr_points) >= 3:
                    DXFPatternImporter._add_piece(pieces, curr_points, curr_layer, piece_idx, scale_factor)
                    piece_idx += 1

                curr_entity = val
                curr_points = []
                curr_layer = "0"
                is_closed = False

            elif code == "8":  # Layer name
                curr_layer = val.upper()

            elif code == "70":  # Flags
                try:
                    flags = int(val)
                    if flags & 1:
                        is_closed = True
                except ValueError:
                    pass

            elif curr_entity == "LWPOLYLINE":
                if code == "10":  # X coord
                    try:
                        x = float(val)
                        # Read Y coord
                        if i < n - 1 and lines[i].strip() == "20":
                            y = float(lines[i + 1].strip())
                            i += 2
                            curr_points.append((x, y))
                    except ValueError:
                        pass

        # Handle last entity
        if curr_entity in ("LWPOLYLINE", "POLYLINE") and len(curr_points) >= 3:
            DXFPatternImporter._add_piece(pieces, curr_points, curr_layer, piece_idx, scale_factor)

        return pieces

    @staticmethod
    def _add_piece(
        pieces: List[GarmentPiece],
        raw_pts: List[Point],
        layer: str,
        idx: int,
        scale: float,
    ) -> None:
        scaled_pts = [(p[0] * scale, p[1] * scale) for p in raw_pts]
        bounds = polygon_bounds(scaled_pts)
        min_x, min_y = bounds[0], bounds[1]
        norm_pts = [(round(p[0] - min_x, 2), round(p[1] - min_y, 2)) for p in scaled_pts]

        piece = GarmentPiece(
            id=f"dxf_piece_{idx}",
            name=f"Pattern Piece {idx} ({layer})",
            category="body",
            raw_vertices=norm_pts,
            design_phase=(0.0, 0.0),
            allowed_rotations=[0.0],
            color_tag=SVGPatternImporter._pick_color(idx),
            metadata={"source_layer": layer},
        )
        pieces.append(piece)


class JSONPatternImporter:
    """Loads and validates full digital pattern project files."""

    @staticmethod
    def parse_json(json_content: str) -> Tuple[List[GarmentPiece], List[Dict[str, Any]], Dict[str, Any]]:
        data = json.loads(json_content)
        pieces_data = data.get("pieces", [])
        contracts_data = data.get("contracts", [])
        metadata = data.get("metadata", {})

        pieces: List[GarmentPiece] = []
        for p in pieces_data:
            phase = (p.get("design_phase", {}).get("u", 0.0), p.get("design_phase", {}).get("v", 0.0))
            piece = GarmentPiece(
                id=p["id"],
                name=p["name"],
                category=p.get("category", "body"),
                raw_vertices=[(pt[0], pt[1]) for pt in p["vertices"]],
                design_phase=phase,
                allowed_rotations=p.get("allowed_rotations", [0.0]),
                color_tag=p.get("color_tag", "#38bdf8"),
            )
            pieces.append(piece)

        return (pieces, contracts_data, metadata)
