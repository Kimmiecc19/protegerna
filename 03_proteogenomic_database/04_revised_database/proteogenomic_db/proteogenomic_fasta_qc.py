"""Compatibility facade and executable entry point for FASTA QC."""
from __future__ import annotations
import importlib
from proteogenomic.qc_pipeline import main
from proteogenomic.qc_cli import parse_args  # noqa: F401  (compatibility export)

_COMPATIBILITY_MODULES = (
    "proteogenomic.qc_models", "proteogenomic.qc_io",
    "proteogenomic.qc_calculations", "proteogenomic.qc_reporting",
)

def __getattr__(name):
    for module_name in _COMPATIBILITY_MODULES:
        module = importlib.import_module(module_name)
        if not name.startswith("_") and hasattr(module, name):
            return getattr(module, name)
    raise AttributeError(name)

if __name__ == "__main__":
    main()
