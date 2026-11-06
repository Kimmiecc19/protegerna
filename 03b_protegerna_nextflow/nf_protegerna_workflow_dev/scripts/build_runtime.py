#!/usr/bin/env python3
"""Rebuild the bundled runtime, the publication defaults and the params template.

Run from the pipeline root (Python >= 3.11 with the pinned dependencies):

    python scripts/build_runtime.py [--source DIR] [--toml FILE]

Writes:
  assets/proteogenomic_runtime/              unmodified copies of the reconstruction modules the
                                             pipeline can reach, plus nextflow_adapter.py and
                                             SOURCE_MANIFEST.json (SHA-256 of every bundled file)
  assets/resolved_publication_defaults.json  every stage option: parser default overlaid with the
                                             frozen publication TOML (the single source of defaults)
  assets/params.publication.yml              params-file template listing every parameter

The source directory is never modified and no file is patched: the bundle is a byte-identical
subset of the source, selected by following imports from the stages in nextflow_adapter.py.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import shutil
import sys
import tomllib
from pathlib import Path

root = Path.cwd()
ap = argparse.ArgumentParser()
ap.add_argument("--source", type=Path, default=root.parent / "code_proteogenomic_database_v7")
ap.add_argument("--toml", type=Path, default=root / "assets/workflow.publication.v5.toml",
                help="frozen publication configuration (default: assets/workflow.publication.v5.toml)")
args = ap.parse_args()
src = args.source.resolve()
toml_path = args.toml.resolve()
overlay = root / "assets/runtime_overlay"
adapter = overlay / "nextflow_adapter.py"
if not (root / "main.nf").exists():
    sys.exit("Run from the nf-core-protegerna root")
for p in (src / "proteogenomic_workflow.py", toml_path, adapter):
    if not p.exists():
        sys.exit(f"Missing: {p}")


# --- Select the modules reachable from the adapter's stages -------------------------------
def module_path(name: str) -> Path | None:
    path = src / (name.replace(".", "/") + ".py")
    return path if path.is_file() else None


def imports(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            base = ("proteogenomic." + (node.module or "")) if node.level else (node.module or "")
            base = base.rstrip(".")
            found.add(base)
            found.update(f"{base}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
    return {name for name in found if module_path(name)}


stages = next(node.value for node in ast.walk(ast.parse(adapter.read_text()))
              if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "STAGES")
entry = {element.value for item in ast.literal_eval(stages).values() for element in map(ast.Constant, item)}
entry |= imports(adapter) | {"proteogenomic.splice_translation", "proteogenomic.provenance"}
selected, pending = set(), [name for name in entry if module_path(name)]
while pending:
    name = pending.pop()
    if name not in selected:
        selected.add(name)
        pending.extend(imports(module_path(name)))
if (src / "proteogenomic/__init__.py").exists():
    selected.add("proteogenomic")
files = sorted({module_path(name) or src / "proteogenomic/__init__.py" for name in selected})

dest = root / "assets/proteogenomic_runtime"
# Remove old files but not folders: on Windows, OneDrive or an open Explorer window can
# lock a folder so it cannot be deleted even though the files inside it can.
if dest.exists():
    for old in sorted(dest.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if old.is_dir() and not old.is_symlink():
            try:
                old.rmdir()  # only succeeds when empty and not locked; otherwise kept
            except OSError:
                pass
        else:
            old.unlink()
for p in files:
    target = dest / p.relative_to(src)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
for p in sorted(overlay.iterdir()):
    shutil.copy2(p, dest / p.name)

bundled = {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(dest.rglob("*")) if p.is_file()}
source = {p.relative_to(src).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
assert all(bundled[k] == v for k, v in source.items()), "bundled copy differs from source"
omitted = sorted(p.relative_to(src).as_posix() for p in [*src.glob("*.py"), *(src / "proteogenomic").glob("*.py")]
                 if p not in files)
(dest / "SOURCE_MANIFEST.json").write_text(json.dumps({
    "source": os.path.relpath(src, root).replace(os.sep, "/"),
    "release_configuration": os.path.relpath(toml_path, root).replace(os.sep, "/"),
    "source_sha256": source,
    "pipeline_files": sorted(set(bundled) - set(source)),
    "not_bundled_unused_by_pipeline": omitted,
}, indent=2) + "\n")

if toml_path != (root / "assets/workflow.publication.v5.toml").resolve():
    shutil.copy2(toml_path, root / "assets/workflow.publication.v5.toml")
release = tomllib.loads(toml_path.read_text())

# --- Publication defaults: parser defaults overlaid with the frozen TOML --------------------
sys.path.insert(0, str(src))
from proteogenomic_workflow import INPUT_KEYS, PARSERS  # noqa: E402

skip = {"reference_peptide_cache", "sample_metadata", "annotation_release", "organism"}
outputs = {"filtered_protein_fasta", "filtered_cds_fasta", "biological_interpretation_tsv",
           "dia_database_metadata_tsv", "digested_peptide_tsv", "transcript_model_cache", "outdir"}
defaults: dict[str, dict] = {}
for step in ["validate", "fusion", "rmats", "suppa", "merge", "qc"]:
    mod, factory = PARSERS[step]
    parser = getattr(importlib.import_module(mod), factory)()
    values = {a.dest: a.default for a in parser._actions
              if a.dest != "help" and a.dest not in INPUT_KEYS[step] and a.dest not in skip}
    for k, v in release.get(step, {}).items():
        if k in values:
            values[k] = v
    for k, v in list(values.items()):
        if (k.startswith("out_") or k in outputs) and isinstance(v, str):
            values[k] = Path(v).name
    values.pop("transcript_model_cache", None)  # pre-2026-10-12 sources: accepted but never used
    values.pop("event_metadata", None)  # written by the pipeline from the samplesheet
    defaults[step] = values
defaults["fusion"].update(out_sequence_sample_tsv="fusion.sequence_samples.tsv", digested_peptide_tsv="fusion.peptides.tsv")
defaults["rmats"].update(out_alt_start_prot_fa="rmats.alternative_start.fasta",
                         out_exploratory_orf_fa="rmats.exploratory_orf.fasta", out_junc_fa="rmats.junctions.fasta")
defaults["suppa"].update(out_alt_start_prot_fa="suppa.alternative_start.fasta",
                         out_exploratory_orf_fa="suppa.exploratory_orf.fasta", out_junc_fa="suppa.junctions.fasta")
defaults["qc"]["outdir"] = "qc"
(root / "assets/resolved_publication_defaults.json").write_text(json.dumps(defaults, indent=2, default=str) + "\n")

print(f"Bundled {len(files)} of {len(files) + len(omitted)} source modules from {src}")
print(f"Not bundled (unused by the pipeline): {', '.join(omitted)}")
print("Wrote assets/resolved_publication_defaults.json")


# ---------------------------------------------------------------------------
# assets/params.publication.yml: every user-settable parameter, publication values.
# ---------------------------------------------------------------------------
def _yaml(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(_yaml(v) for v in value) + "]"
    return "'" + str(value).replace("'", "''") + "'"


CORE = [
    ("Inputs and references (paths on the server)", [
        ("input", "/path/to/samplesheet.csv", "sample,tool,event_type,path,batch,condition (see README)"),
        ("outdir", "results/protegerna_publication", None),
        ("genome", "/path/to/GRCh38.primary_assembly.genome.fa", "uncompressed"),
        ("gtf", "/path/to/gencode.v46.annotation.gtf", "give exactly one of gtf / gtf_db"),
        ("gtf_db", None, "prebuilt gffutils database"),
        ("reference_proteome", "/path/to/reference_proteome.fasta", "uncompressed target proteome"),
        ("gencode_protein_fasta", "/path/to/gencode.v46.pc_translations.fa.gz", None),
        ("contaminants", "/path/to/crap.fasta", "optional; null to omit"),
        ("sample_metadata", None, "optional sample_id,batch,condition table"),
        ("reference_peptide_cache", None, "optional reuse of a previous cache"),
        ("annotation_release", "GENCODE_46", None),
        ("organism", "Homo_sapiens", None),
    ]),
    ("Runtime", [
        ("proteogenomic_container", "/absolute/path/protegerna.sif", None),
        ("max_cpus", 8, None),
        ("max_memory", "32.GB", None),
        ("publish_dir_mode", "copy", None),
    ]),
    ("Reference-peptide digestion and samplesheet checks", [
        ("min_peptide_length", 7, None),
        ("max_peptide_length", 40, None),
        ("max_missed_cleavages", 3, None),
        ("suppa_require_psi", True, "false only for an intentionally unfiltered SUPPA run"),
    ]),
]
lines = [
    "# nf-core/protegerna - publication parameters",
    "#",
    "#   nextflow run . -profile publication -params-file params.yml -resume",
    "#",
    "# Generated by scripts/build_runtime.py. Values below the stage headings are the",
    "# frozen publication policy (assets/resolved_publication_defaults.json). Edit any",
    "# value; delete a line to keep its publication default. Unknown keys stop the run.",
    "# Output names under the stages must be plain file names; outdir sets the location.",
    "",
]
for title, entries in CORE:
    lines.append(f"# --- {title}")
    for key, value, note in entries:
        lines.append(f"{key}: {_yaml(value)}" + (f"  # {note}" if note else ""))
    lines.append("")
for step in ["validate", "fusion", "rmats", "suppa", "merge", "qc"]:
    lines.append(f"# --- {step} options")
    lines.append(f"{step}:")
    for key, value in defaults[step].items():
        lines.append(f"  {key}: {_yaml(value)}")
    lines.append("")
(root / "assets/params.publication.yml").write_text("\n".join(lines))
print("Wrote assets/params.publication.yml")
