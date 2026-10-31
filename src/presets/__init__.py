"""Preset registry for Garment Pattern Nesting."""

from typing import Dict, Any, List, Tuple
from .plaid_shirt import create_plaid_shirt_preset
from .striped_tee import create_striped_tee_preset
from .floral_dress import create_floral_dress_preset
from ..core.pieces import GarmentPiece
from ..core.seam_contracts import SeamContract

PRESET_FACTORIES = {
    "plaid_oxford_shirt": create_plaid_shirt_preset,
    "breton_striped_tee": create_striped_tee_preset,
    "botanical_floral_dress": create_floral_dress_preset,
}


def list_presets() -> List[Dict[str, Any]]:
    """Return overview metadata for all bundled presets."""
    result = []
    for pid, factory in PRESET_FACTORIES.items():
        _, _, meta = factory()
        result.append(meta)
    return result


def load_preset(preset_id: str) -> Tuple[List[GarmentPiece], List[SeamContract], Dict[str, Any]]:
    """Instantiate and return (pieces, contracts, metadata) for given preset_id."""
    if preset_id not in PRESET_FACTORIES:
        raise ValueError(f"Unknown preset ID '{preset_id}'. Available: {list(PRESET_FACTORIES.keys())}")
    return PRESET_FACTORIES[preset_id]()
