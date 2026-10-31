"""Compatibility facade and executable entry point for fusion reconstruction."""
from __future__ import annotations
import importlib
from proteogenomic.fusion_models import PARSED_FUSION_COLUMNS
from proteogenomic.fusion_parsing import parse_fusioninspector as _parse_fusioninspector
from proteogenomic.fusion_pipeline import main

_COMPATIBILITY_MODULES = (
    "proteogenomic.fusion_models", "proteogenomic.fusion_values",
    "proteogenomic.fusion_coordinates", "proteogenomic.fusion_transcripts",
    "proteogenomic.fusion_filtering", "proteogenomic.fusion_candidate_evaluation",
    "proteogenomic.fusion_orchestration", "proteogenomic.fusion_reporting",
    "proteogenomic.fusion_cli",
)

def parse_fusioninspector(frame):
    return _parse_fusioninspector(frame, PARSED_FUSION_COLUMNS)

def __getattr__(name):
    """Resolve non-private legacy API names from their owning module."""
    for module_name in _COMPATIBILITY_MODULES:
        module = importlib.import_module(module_name)
        if not name.startswith("_") and hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(name)

if __name__ == "__main__":
    raise SystemExit(main())
