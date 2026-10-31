"""Plaid Oxford Button-Up Shirt Preset with Calibrated Phase Contracts."""

from typing import List, Dict, Any, Tuple
from ..core.pieces import GarmentPiece, MatchNotch
from ..core.seam_contracts import SeamContract

# Master Repeat Dimensions in mm
REPEAT_WIDTH_MM = 100.0
REPEAT_HEIGHT_MM = 100.0
FABRIC_WIDTH_MM = 1480.0  # 58-inch standard roll cuttable width


def create_plaid_shirt_preset() -> Tuple[List[GarmentPiece], List[SeamContract], Dict[str, Any]]:
    """Return pieces, seam contracts, and repeat metadata for Plaid Oxford Shirt."""

    # 1. Front Left (with Placket)
    # Origin (0,0) at bottom-left hem
    front_left_verts = [
        (0.0, 0.0),        # Bottom CF
        (290.0, 0.0),      # Bottom Side seam
        (280.0, 420.0),    # Waist side seam
        (285.0, 490.0),    # Underarm point
        (220.0, 560.0),    # Armhole curve mid
        (190.0, 680.0),    # Shoulder tip
        (75.0, 715.0),     # Neck shoulder point
        (0.0, 640.0),      # Front neck drop at CF
    ]

    # 2. Front Right
    front_right_verts = [
        (0.0, 0.0),        # Bottom CF
        (270.0, 0.0),      # Bottom Side seam
        (260.0, 420.0),    # Waist side seam
        (265.0, 490.0),    # Underarm point
        (205.0, 560.0),    # Armhole curve mid
        (175.0, 680.0),    # Shoulder tip
        (60.0, 715.0),     # Neck shoulder point
        (0.0, 640.0),      # Front neck drop at CF
    ]

    # 3. Patch Pocket (Left Chest)
    pocket_verts = [
        (0.0, 0.0),        # Top Left
        (130.0, 0.0),      # Top Right
        (130.0, 120.0),    # Right hem start
        (65.0, 150.0),     # Bottom V-point
        (0.0, 120.0),      # Left hem start
    ]

    # 4. Back Body Panel
    back_body_verts = [
        (0.0, 0.0),        # Bottom Left side seam
        (540.0, 0.0),      # Bottom Right side seam
        (530.0, 420.0),    # Right waist side seam
        (535.0, 490.0),    # Right underarm
        (470.0, 560.0),    # Right armhole mid
        (450.0, 630.0),    # Right yoke seam edge
        (90.0, 630.0),     # Left yoke seam edge
        (70.0, 560.0),     # Left armhole mid
        (5.0, 490.0),      # Left underarm
        (10.0, 420.0),     # Left waist side seam
    ]

    # 5. Back Yoke
    back_yoke_verts = [
        (0.0, 0.0),        # Bottom Left (meets back body)
        (480.0, 0.0),      # Bottom Right (meets back body)
        (450.0, 120.0),    # Right shoulder tip
        (290.0, 135.0),    # Right back neck
        (190.0, 135.0),    # Left back neck
        (30.0, 120.0),     # Left shoulder tip
    ]

    # 6. Left Sleeve
    sleeve_left_verts = [
        (30.0, 0.0),       # Cuff Left
        (260.0, 0.0),      # Cuff Right
        (380.0, 420.0),    # Underarm Right
        (300.0, 520.0),    # Bicep cap Right
        (190.0, 570.0),    # Sleeve cap Apex
        (80.0, 520.0),     # Bicep cap Left
        (0.0, 420.0),      # Underarm Left
    ]

    # 7. Right Sleeve
    sleeve_right_verts = [
        (30.0, 0.0),
        (260.0, 0.0),
        (380.0, 420.0),
        (300.0, 520.0),
        (190.0, 570.0),
        (80.0, 520.0),
        (0.0, 420.0),
    ]

    # 8. Collar Leaf & Band
    collar_leaf_verts = [
        (0.0, 0.0),
        (450.0, 0.0),
        (465.0, 55.0),
        (225.0, 50.0),
        (-15.0, 55.0),
    ]

    collar_band_verts = [
        (15.0, 0.0),
        (445.0, 0.0),
        (460.0, 38.0),
        (230.0, 35.0),
        (0.0, 38.0),
    ]

    # Design Texture Phase Offsets (target_u, target_v) in mm
    # In CAD, designer aligned Front Left & Right at CF (u=0.0) with identical vertical stripe phase (v=15.0)
    front_left_phase = (0.0, 15.0)
    front_right_phase = (0.0, 15.0)  # Locked to Front Left

    # Pocket placement notch on Left Front is at local (x=90.0, y=380.0)
    # Pocket phase must equal: (front_left_phase + pocket_loc) % repeat
    pocket_u = (front_left_phase[0] + 90.0) % REPEAT_WIDTH_MM
    pocket_v = (front_left_phase[1] + 380.0) % REPEAT_HEIGHT_MM
    pocket_phase = (pocket_u, pocket_v)

    # Back body aligned horizontally with front body waist (v=15.0)
    back_body_phase = (25.0, 15.0)

    # Yoke meets back body at y=630.0. Phase at yoke bottom:
    yoke_v = (back_body_phase[1] + 630.0) % REPEAT_HEIGHT_MM
    back_yoke_phase = (55.0, yoke_v)

    # Sleeves horizontal stripe match
    sleeve_phase = (50.0, 15.0)
    collar_phase = (0.0, 50.0)

    pieces = [
        GarmentPiece(
            id="front_left",
            name="Front Left (Placket)",
            category="body",
            raw_vertices=front_left_verts,
            design_phase=front_left_phase,
            allowed_rotations=[0.0],
            color_tag="#38bdf8",
            match_notches=[
                MatchNotch("fl_cf_mid", "CF Mid Placket", (0.0, 350.0), "CF"),
                MatchNotch("fl_pocket_anchor", "Pocket Mount", (90.0, 380.0), "CHEST"),
                MatchNotch("fl_waist", "Waist Notch", (280.0, 420.0), "SIDE"),
            ],
            metadata={"pocket_mount_pos": (90.0, 380.0)},
        ),
        GarmentPiece(
            id="front_right",
            name="Front Right",
            category="body",
            raw_vertices=front_right_verts,
            design_phase=front_right_phase,
            allowed_rotations=[0.0],
            color_tag="#0ea5e9",
            match_notches=[
                MatchNotch("fr_cf_mid", "CF Mid Button", (0.0, 350.0), "CF"),
                MatchNotch("fr_waist", "Waist Notch", (260.0, 420.0), "SIDE"),
            ],
        ),
        GarmentPiece(
            id="chest_pocket",
            name="Chest Pocket",
            category="pocket",
            raw_vertices=pocket_verts,
            design_phase=pocket_phase,
            allowed_rotations=[0.0],
            color_tag="#e5a93c",
            match_notches=[
                MatchNotch("p_top_left", "Top Left Stitch", (0.0, 0.0), "TOP"),
            ],
            metadata={"parent_piece_id": "front_left"},
        ),
        GarmentPiece(
            id="back_body",
            name="Back Body",
            category="body",
            raw_vertices=back_body_verts,
            design_phase=back_body_phase,
            allowed_rotations=[0.0],
            color_tag="#818cf8",
            match_notches=[
                MatchNotch("bb_waist_l", "Left Waist", (10.0, 420.0), "SIDE"),
                MatchNotch("bb_yoke_mid", "Yoke Seam Mid", (270.0, 630.0), "YOKE"),
            ],
        ),
        GarmentPiece(
            id="back_yoke",
            name="Back Yoke",
            category="yoke",
            raw_vertices=back_yoke_verts,
            design_phase=back_yoke_phase,
            allowed_rotations=[0.0],
            color_tag="#c084fc",
            match_notches=[
                MatchNotch("by_seam_mid", "Yoke Bottom Mid", (240.0, 0.0), "YOKE"),
            ],
        ),
        GarmentPiece(
            id="sleeve_left",
            name="Left Sleeve",
            category="sleeve",
            raw_vertices=sleeve_left_verts,
            design_phase=sleeve_phase,
            allowed_rotations=[0.0],
            color_tag="#34d399",
        ),
        GarmentPiece(
            id="sleeve_right",
            name="Right Sleeve",
            category="sleeve",
            raw_vertices=sleeve_right_verts,
            design_phase=sleeve_phase,
            allowed_rotations=[0.0],
            color_tag="#10b981",
        ),
        GarmentPiece(
            id="collar_leaf",
            name="Collar Leaf",
            category="collar",
            raw_vertices=collar_leaf_verts,
            design_phase=collar_phase,
            allowed_rotations=[0.0],
            color_tag="#f472b6",
        ),
        GarmentPiece(
            id="collar_band",
            name="Collar Band",
            category="collar",
            raw_vertices=collar_band_verts,
            design_phase=collar_phase,
            allowed_rotations=[0.0],
            color_tag="#fb7185",
        ),
    ]

    contracts = [
        SeamContract(
            id="cf_placket_match",
            name="Placket Stripe Match",
            contract_type="CF_PLACKET",
            piece_a_id="front_left",
            piece_b_id="front_right",
            description="Horizontal and vertical plaid stripes must align across Center Front button stand.",
            expected_delta_uv=(0.0, 0.0),
            tolerance_mm=1.0,
        ),
        SeamContract(
            id="pocket_chest_match",
            name="Pocket 1:1 Chest Continuation",
            contract_type="POCKET_MATCH",
            piece_a_id="chest_pocket",
            piece_b_id="front_left",
            description="Patch pocket plaid pattern must seamlessly continue underlying front chest pattern.",
            expected_delta_uv=(pocket_phase[0] - front_left_phase[0], pocket_phase[1] - front_left_phase[1]),
            tolerance_mm=0.5,
        ),
        SeamContract(
            id="yoke_back_match",
            name="Yoke to Back Seam Flow",
            contract_type="YOKE_CHEVRON",
            piece_a_id="back_yoke",
            piece_b_id="back_body",
            description="Vertical plaid lines flow from back body through shoulder yoke.",
            expected_delta_uv=(back_yoke_phase[0] - back_body_phase[0], back_yoke_phase[1] - back_body_phase[1]),
            tolerance_mm=1.0,
        ),
        SeamContract(
            id="side_seam_waist_match",
            name="Side Seam Horizontal Course",
            contract_type="SIDE_SEAM",
            piece_a_id="front_left",
            piece_b_id="back_body",
            description="Horizontal check stripe meets across front and back side seam at waist notch.",
            expected_delta_uv=((front_left_phase[0] - back_body_phase[0]) % REPEAT_WIDTH_MM, (front_left_phase[1] - back_body_phase[1]) % REPEAT_HEIGHT_MM),
            tolerance_mm=1.5,
        ),
    ]

    metadata = {
        "preset_id": "plaid_oxford_shirt",
        "title": "Tartan Plaid Oxford Shirt",
        "repeat_type": "plaid",
        "repeat_width_mm": REPEAT_WIDTH_MM,
        "repeat_height_mm": REPEAT_HEIGHT_MM,
        "roll_width_mm": FABRIC_WIDTH_MM,
        "pattern_colors": {
            "background": "#0f3a57",   # Deep navy
            "stripe_primary": "#dc2626", # Royal red
            "stripe_secondary": "#e5a93c", # Amber yellow
            "stripe_overcheck": "#ffffff", # White crisp overcheck
        },
        "description": "Men's button-up shirt with strict placket stripe matching and invisible chest pocket pattern alignment.",
    }

    return (pieces, contracts, metadata)
