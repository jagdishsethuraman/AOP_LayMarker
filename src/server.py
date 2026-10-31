"""Zero-Dependency Python HTTP Server and REST API for Pattern Nest Studio.

Hosts interactive local test studio on http://127.0.0.1:8090.
"""

from __future__ import annotations
import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any

from .presets import list_presets, load_preset
from .core.pieces import GarmentPiece
from .core.seam_contracts import SeamContract
from .core.importers import SVGPatternImporter, DXFPatternImporter, JSONPatternImporter
from .nesting.lattice_placer import LatticePlacer
from .nesting.optimizer import NestingOptimizer
from .nesting.validator import SeamValidator

PORT = int(os.environ.get("PORT", 8092))
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")


class StudioHandler(BaseHTTPRequestHandler):
    """Handles REST API requests and serves static web assets."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress noisy request logging, output concise server logs."""
        pass

    def do_GET(self) -> None:
        """Handle GET requests for static files and presets."""
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API: List Presets
        if path == "/api/presets":
            presets = list_presets()
            self._send_json(200, {"presets": presets})
            return

        # REST API: Load Specific Preset
        if path == "/api/preset":
            qs = parse_qs(parsed.query)
            preset_id = qs.get("id", ["plaid_oxford_shirt"])[0]
            try:
                pieces, contracts, metadata = load_preset(preset_id)
                data = {
                    "metadata": metadata,
                    "pieces": [p.to_dict() for p in pieces],
                    "contracts": [c.to_dict() for c in contracts],
                }
                self._send_json(200, data)
            except Exception as e:
                self._send_json(400, {"error": str(e)})
            return

        # Static Web Files
        if path == "/" or path == "":
            file_path = os.path.join(WEB_DIR, "index.html")
        else:
            rel_path = path.lstrip("/")
            file_path = os.path.join(WEB_DIR, rel_path)

        if os.path.isfile(file_path):
            self._serve_file(file_path)
        else:
            self.send_error(404, f"File not found: {path}")

    def do_POST(self) -> None:
        """Handle POST requests for nesting computation and seam validation."""
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON body: {str(e)}"})
            return

        # REST API: Run Nesting
        if path == "/api/nest":
            self._handle_nest(body)
            return

        # REST API: Validate Placement
        if path == "/api/validate":
            self._handle_validate(body)
            return

        # REST API: Import SVG Pattern
        if path == "/api/import/svg":
            svg_text = body.get("svg", "")
            scale = float(body.get("scale", 1.0))
            try:
                pieces = SVGPatternImporter.parse_svg(svg_text, scale)
                self._send_json(200, {
                    "success": True,
                    "pieces": [p.to_dict() for p in pieces],
                    "count": len(pieces),
                })
            except Exception as e:
                self._send_json(400, {"error": f"SVG Import failed: {str(e)}"})
            return

        # REST API: Import DXF Pattern
        if path == "/api/import/dxf":
            dxf_text = body.get("dxf", "")
            scale = float(body.get("scale", 1.0))
            try:
                pieces = DXFPatternImporter.parse_dxf(dxf_text, scale)
                self._send_json(200, {
                    "success": True,
                    "pieces": [p.to_dict() for p in pieces],
                    "count": len(pieces),
                })
            except Exception as e:
                self._send_json(400, {"error": f"DXF Import failed: {str(e)}"})
            return

        # REST API: Import JSON Full Project
        if path == "/api/import/json":
            json_text = body.get("json", "")
            try:
                pieces, contracts, meta = JSONPatternImporter.parse_json(json_text)
                self._send_json(200, {
                    "success": True,
                    "pieces": [p.to_dict() for p in pieces],
                    "contracts": contracts,
                    "metadata": meta,
                })
            except Exception as e:
                self._send_json(400, {"error": f"JSON Import failed: {str(e)}"})
            return

        self.send_error(404, f"Endpoint not found: {path}")

    def _handle_nest(self, body: Dict[str, Any]) -> None:
        """Execute Phase-Locked Nesting on server (preset or custom imported pieces)."""
        custom_pieces_data = body.get("custom_pieces")
        custom_contracts_data = body.get("custom_contracts")

        if custom_pieces_data:
            # Reconstruct pieces from payload
            pieces = []
            for p in custom_pieces_data:
                phase = (p.get("design_phase", {}).get("u", 0.0), p.get("design_phase", {}).get("v", 0.0))
                pieces.append(GarmentPiece(
                    id=p["id"],
                    name=p["name"],
                    category=p.get("category", "body"),
                    raw_vertices=[(pt[0], pt[1]) for pt in p["vertices"]],
                    design_phase=phase,
                    allowed_rotations=p.get("allowed_rotations", [0.0]),
                    color_tag=p.get("color_tag", "#38bdf8"),
                ))
            contracts = []
            if custom_contracts_data:
                for c in custom_contracts_data:
                    contracts.append(SeamContract(
                        id=c["id"],
                        name=c["name"],
                        contract_type=c.get("contract_type", "CUSTOM"),
                        piece_a_id=c["piece_a_id"],
                        piece_b_id=c["piece_b_id"],
                        description=c.get("description", ""),
                        expected_delta_uv=tuple(c.get("expected_delta_uv", [0.0, 0.0])),
                        tolerance_mm=float(c.get("tolerance_mm", 1.0)),
                    ))
            meta = {
                "roll_width_mm": float(body.get("roll_width_mm", 1480.0)),
                "repeat_width_mm": float(body.get("repeat_width_mm", 100.0)),
                "repeat_height_mm": float(body.get("repeat_height_mm", 100.0)),
            }
        else:
            preset_id = body.get("preset_id", "plaid_oxford_shirt")
            try:
                pieces, contracts, meta = load_preset(preset_id)
            except Exception as e:
                self._send_json(400, {"error": f"Failed to load preset: {str(e)}"})
                return

        roll_width = float(body.get("roll_width_mm", meta["roll_width_mm"]))
        repeat_w = float(body.get("repeat_width_mm", meta["repeat_width_mm"]))
        repeat_h = float(body.get("repeat_height_mm", meta["repeat_height_mm"]))
        buffer_mm = float(body.get("buffer_mm", 4.0))
        optimize = bool(body.get("optimize", True))

        placer = LatticePlacer(
            roll_width_mm=roll_width,
            repeat_w_mm=repeat_w,
            repeat_h_mm=repeat_h,
            margin_left_mm=10.0,
            margin_right_mm=10.0,
            buffer_mm=buffer_mm,
        )

        try:
            if optimize:
                optimizer = NestingOptimizer(placer)
                marker_res = optimizer.optimize(pieces, max_iterations=12, time_limit_sec=1.5)
            else:
                marker_res = placer.place_pieces(pieces, priority_first=True)

            # Validate all seam contracts
            validation = SeamValidator.validate_marker(
                marker_res.placed_pieces,
                contracts,
                repeat_w_mm=repeat_w,
                repeat_h_mm=repeat_h,
            )

            response = {
                "success": True,
                "marker": marker_res.to_dict(),
                "validation": validation,
                "metadata": meta,
            }
            self._send_json(200, response)

        except Exception as e:
            self._send_json(500, {"error": f"Nesting failed: {str(e)}"})

    def _handle_validate(self, body: Dict[str, Any]) -> None:
        """Validate live manual placement positions."""
        preset_id = body.get("preset_id", "plaid_oxford_shirt")
        placements = body.get("placements", {})  # { piece_id: [x, y] }
        repeat_w = float(body.get("repeat_width_mm", 100.0))
        repeat_h = float(body.get("repeat_height_mm", 100.0))

        try:
            _, contracts, _ = load_preset(preset_id)
        except Exception as e:
            self._send_json(400, {"error": str(e)})
            return

        results = []
        all_passed = True
        max_mismatch = 0.0

        for contract in contracts:
            if contract.piece_a_id in placements and contract.piece_b_id in placements:
                pos_a = tuple(placements[contract.piece_a_id])
                pos_b = tuple(placements[contract.piece_b_id])
                eval_res = contract.evaluate(pos_a, pos_b, repeat_w, repeat_h)
                results.append(eval_res)
                if not eval_res["passed"]:
                    all_passed = False
                if eval_res["mismatch_mm"] > max_mismatch:
                    max_mismatch = eval_res["mismatch_mm"]

        self._send_json(200, {
            "all_passed": all_passed,
            "max_mismatch_mm": round(max_mismatch, 3),
            "evaluations": results,
        })

    def _serve_file(self, file_path: str) -> None:
        """Serve a static file with correct MIME type."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")

    def _send_json(self, status: int, data: Dict[str, Any]) -> None:
        """Send JSON response."""
        resp = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp)


def run_server(port: int = PORT) -> None:
    """Start local development server."""
    server = HTTPServer((HOST, port), StudioHandler)
    print(f"⚡ PatternNest Studio running at http://{HOST}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
