"""Breton Sailor Striped T-Shirt Preset with Horizontal Seam Matching."""

from typing import List, Dict, Any, Tuple
from ..core.pieces import GarmentPiece, MatchNotch
from ..core.seam_contracts import SeamContract

REPEAT_WIDTH_MM = 60.0
REPEAT_HEIGHT_MM = 40.0  # Horizontal stripe repeat pitch: 20mm Navy / 20mm White
FABRIC_WIDTH_MM = 1520.0  # 60-inch knit fabric cuttable roll width


def create_striped_tee_preset() -> Tuple[List[GarmentPiece], List[SeamContract], Dict[str, Any]]:
    """Return pieces, seam contracts, and metadata for Breton Sailor Striped T-Shirt."""

    # 1. Front Body
    front_body_verts = [
        (0.0, 0.0),        # Bottom Hem Left
        (520.0, 0.0),      # Bottom Hem Right
        (510.0, 420.0),    # Waist Right
        (520.0, 480.0),    # Underarm Right
        (450.0, 560.0),    # Armhole mid Right
        (410.0, 680.0),    # Shoulder tip Right
        (310.0, 700.0),    # Neck Right
        (260.0, 600.0),    # Front Neck Drop
        (210.0, 700.0),    # Neck Left
        (110.0, 680.0),    # Shoulder tip Left
        (70.0, 560.0),     # Armhole mid Left
        (0.0, 480.0),      # Underarm Left
        (10.0, 420.0),     # Waist Left
    ]

    # 2. Back Body
    back_body_verts = [
        (0.0, 0.0),        # Bottom Hem Left
        (520.0, 0.0),      # Bottom Hem Right
        (510.0, 420.0),    # Waist Right
        (520.0, 480.0),    # Underarm Right
        (450.0, 560.0),    # Armhole mid Right
        (410.0, 680.0),    # Shoulder tip Right
        (310.0, 700.0),    # Neck Right
        (260.0, 665.0),    # Back Neck Drop (shallow)
        (210.0, 700.0),    # Neck Left
        (110.0, 680.0),    # Shoulder tip Left
        (70.0, 560.0),     # Armhole mid Left
        (0.0, 480.0),      # Underarm Left
        (10.0, 420.0),     # Waist Left
    ]

    # 3. Left Sleeve
    sleeve_left_verts = [
        (0.0, 0.0),        # Cuff Left
        (340.0, 0.0),      # Cuff Right
        (380.0, 200.0),    # Underarm Right
        (290.0, 280.0),    # Cap Right
        (170.0, 310.0),    # Apex
        (50.0, 280.0),     # Cap Left
        (-40.0, 200.0),    # Underarm Left
    ]

    # 4. Right Sleeve
    sleeve_right_verts = [
        (0.0, 0.0),
        (340.0, 0.0),
        (380.0, 200.0),
        (290.0, 280.0),
        (170.0, 310.0),
        (50.0, 280.0),
        (-40.0, 200.0),
    ]

    # 5. Neck Rib Band
    neckband_verts = [
        (0.0, 0.0),
        (440.0, 0.0),
        (440.0, 30.0),
        (0.0, 30.0),
    ]

    # Horizontal phase alignment: Both hem lines start at exact same stripe phase (v=0.0)
    front_phase = (0.0, 0.0)
    back_phase = (0.0, 0.0)
    sleeve_phase = (0.0, 0.0)
    neckband_phase = (0.0, 10.0)

    pieces = [
        GarmentPiece(
            id="tee_front",
            name="Front Body",
            category="body",
            raw_vertices=front_body_verts,
            design_phase=front_phase,
            allowed_rotations=[0.0],
            color_tag="#38bdf8",
            match_notches=[
                MatchNotch("tf_waist_r", "Waist Right", (510.0, 420.0), "SIDE"),
                MatchNotch("tf_underarm_r", "Underarm Right", (520.0, 480.0), "ARMHOLE"),
            ],
        ),
        GarmentPiece(
            id="tee_back",
            name="Back Body",
            category="body",
            raw_vertices=back_body_verts,
            design_phase=back_phase,
            allowed_rotations=[0.0],
            color_tag="#818cf8",
            match_notches=[
                MatchNotch("tb_waist_r", "Waist Right", (510.0, 420.0), "SIDE"),
                MatchNotch("tb_underarm_r", "Underarm Right", (520.0, 480.0), "ARMHOLE"),
            ],
        ),
        GarmentPiece(
            id="tee_sleeve_l",
            name="Left Sleeve",
            category="sleeve",
            raw_vertices=sleeve_left_verts,
            design_phase=sleeve_phase,
            allowed_rotations=[0.0],
            color_tag="#34d399",
        ),
        GarmentPiece(
            id="tee_sleeve_r",
            name="Right Sleeve",
            category="sleeve",
            raw_vertices=sleeve_right_verts,
            design_phase=sleeve_phase,
            allowed_rotations=[0.0],
            color_tag="#10b981",
        ),
        GarmentPiece(
            id="tee_neckband",
            name="Neck Rib Band",
            category="collar",
            raw_vertices=neckband_verts,
            design_phase=neckband_phase,
            allowed_rotations=[0.0],
            color_tag="#f59e0b",
        ),
    ]

    contracts = [
        SeamContract(
            id="tee_side_seam_match",
            name="Side Seam Stripe Continuity",
            contract_type="SIDE_SEAM",
            piece_a_id="tee_front",
            piece_b_id="tee_back",
            description="Horizontal navy/white stripe lines match 100% across front and back side seam.",
            expected_delta_uv=(0.0, 0.0),
            tolerance_mm=1.0,
        ),
        SeamContract(
            id="tee_sleeve_match",
            name="Sleeve to Chest Stripe Alignment",
            contract_type="SLEEVE_CHEST",
            piece_a_id="tee_sleeve_l",
            piece_b_id="tee_front",
            description="Bicep horizontal stripes align with front chest level when arm is down.",
            expected_delta_uv=(0.0, 0.0),
            tolerance_mm=1.5,
        ),
    ]

    metadata = {
        "preset_id": "breton_striped_tee",
        "title": "Breton Sailor Striped T-Shirt",
        "repeat_type": "horizontal_stripe",
        "repeat_width_mm": REPEAT_WIDTH_MM,
        "repeat_height_mm": REPEAT_HEIGHT_MM,
        "roll_width_mm": FABRIC_WIDTH_MM,
        "pattern_colors": {
            "background": "#f8fafc",     # Off-white
            "stripe_primary": "#1e3a8a", # Nautical deep navy
        },
        "description": "Classic French sailor nautical tee with uninterrupted horizontal stripes across body side seams.",
    }

    return (pieces, contracts, metadata)
