"""Engineered Botanical Floral AOP Dress Preset."""

from typing import List, Dict, Any, Tuple
from ..core.pieces import GarmentPiece, MatchNotch
from ..core.seam_contracts import SeamContract

REPEAT_WIDTH_MM = 180.0
REPEAT_HEIGHT_MM = 180.0
FABRIC_WIDTH_MM = 1450.0


def create_floral_dress_preset() -> Tuple[List[GarmentPiece], List[SeamContract], Dict[str, Any]]:
    """Return pieces, seam contracts, and metadata for Botanical Floral Dress."""

    # 1. Bodice Front
    bodice_front_verts = [
        (0.0, 0.0),        # Waist CF
        (240.0, 0.0),      # Waist Side
        (255.0, 220.0),    # Underarm
        (210.0, 320.0),    # Armhole mid
        (170.0, 420.0),    # Shoulder tip
        (90.0, 435.0),     # Neck point
        (0.0, 310.0),      # Front neck CF
    ]

    # 2. Bodice Back
    bodice_back_verts = [
        (0.0, 0.0),        # Waist CB
        (240.0, 0.0),      # Waist Side
        (255.0, 220.0),    # Underarm
        (210.0, 320.0),    # Armhole mid
        (170.0, 420.0),    # Shoulder tip
        (90.0, 435.0),     # Neck point
        (0.0, 390.0),      # Back neck CB
    ]

    # 3. Flared Skirt Front
    skirt_front_verts = [
        (0.0, 0.0),        # Hem CF
        (480.0, 0.0),      # Hem Side
        (380.0, 350.0),    # Hip Side
        (240.0, 600.0),    # Waist Side
        (0.0, 600.0),      # Waist CF
    ]

    # 4. Flared Skirt Back
    skirt_back_verts = [
        (0.0, 0.0),        # Hem CB
        (480.0, 0.0),      # Hem Side
        (380.0, 350.0),    # Hip Side
        (240.0, 600.0),    # Waist Side
        (0.0, 600.0),      # Waist CB
    ]

    # Phase design: Bodice waist meets Skirt waist.
    # Bodice bottom hem (y=0) meets Skirt top (y=600)
    bodice_phase = (0.0, 30.0)
    # Skirt top phase should match bodice waist phase
    skirt_v = (bodice_phase[1] - 600.0) % REPEAT_HEIGHT_MM
    skirt_phase = (0.0, skirt_v)

    pieces = [
        GarmentPiece(
            id="bodice_front",
            name="Bodice Front",
            category="body",
            raw_vertices=bodice_front_verts,
            design_phase=bodice_phase,
            allowed_rotations=[0.0],
            color_tag="#ec4899",
            match_notches=[
                MatchNotch("bf_waist_cf", "Waist CF", (0.0, 0.0), "WAIST"),
                MatchNotch("bf_waist_side", "Waist Side", (240.0, 0.0), "SIDE"),
            ],
        ),
        GarmentPiece(
            id="bodice_back",
            name="Bodice Back",
            category="body",
            raw_vertices=bodice_back_verts,
            design_phase=bodice_phase,
            allowed_rotations=[0.0],
            color_tag="#d946ef",
            match_notches=[
                MatchNotch("bb_waist_side", "Waist Side", (240.0, 0.0), "SIDE"),
            ],
        ),
        GarmentPiece(
            id="skirt_front",
            name="Skirt Front",
            category="skirt",
            raw_vertices=skirt_front_verts,
            design_phase=skirt_phase,
            allowed_rotations=[0.0],
            color_tag="#a855f7",
            match_notches=[
                MatchNotch("sf_waist_cf", "Waist CF", (0.0, 600.0), "WAIST"),
            ],
        ),
        GarmentPiece(
            id="skirt_back",
            name="Skirt Back",
            category="skirt",
            raw_vertices=skirt_back_verts,
            design_phase=skirt_phase,
            allowed_rotations=[0.0],
            color_tag="#8b5cf6",
        ),
    ]

    contracts = [
        SeamContract(
            id="waist_motif_flow",
            name="Waistline Floral Motif Continuation",
            contract_type="WAIST_MATCH",
            piece_a_id="bodice_front",
            piece_b_id="skirt_front",
            description="Continuous botanical branch/bloom flows seamlessly from bodice down through skirt panel.",
            expected_delta_uv=((bodice_phase[0] - skirt_phase[0]) % REPEAT_WIDTH_MM, (bodice_phase[1] - skirt_phase[1]) % REPEAT_HEIGHT_MM),
            tolerance_mm=1.0,
        ),
    ]

    metadata = {
        "preset_id": "botanical_floral_dress",
        "title": "Botanical Floral AOP Dress",
        "repeat_type": "floral_tile",
        "repeat_width_mm": REPEAT_WIDTH_MM,
        "repeat_height_mm": REPEAT_HEIGHT_MM,
        "roll_width_mm": FABRIC_WIDTH_MM,
        "pattern_colors": {
            "background": "#141e24",     # Dark botanical teal
            "stripe_primary": "#f43f5e", # Rose bloom
            "stripe_secondary": "#10b981", # Emerald foliage
        },
        "description": "Engineered floral dress requiring vertical stem and bloom alignment across the horizontal waistline seam.",
    }

    return (pieces, contracts, metadata)
