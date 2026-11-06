"""Fusion input discovery, worker lifecycle, and sample orchestration."""
from __future__ import annotations
import glob
import logging
import multiprocessing
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd
from gffutils import FeatureDB
from .fusion_models import (
    CandidatePairRequest, PARSED_FUSION_COLUMNS, PartnerLookupContext,
    PartnerRequest, ReferenceContext, SampleProcessingContext,
)
from .fusion_candidate_evaluation import (
    collect_partner_candidates, evaluate_candidate_pair, log_fusion_progress,
    parse_fusion_row_context, record_skip,
)
from .fusion_filtering import deduplicate_fusions
from .fusion_parsing import parse_fusioninspector as parse_fusioninspector_rows
from .audit import FailureLedger
try:
 from pyfaidx import Fasta
except ImportError: Fasta=None
LOGGER=logging.getLogger(__name__); logger=LOGGER

def parse_fusioninspector(frame):
    return parse_fusioninspector_rows(frame, PARSED_FUSION_COLUMNS)


_WORKER_CONTEXT = {}

def fusioninspector_input_matches(path):
    """
    Return True if a file appears to be a FusionInspector TSV.
    """

    name = Path(path).name.lower()

    return (
        # Filtered outputs
        name.endswith(".fusioninspector.fusions.tsv")
        or name.endswith(".fusioninspector.fusions.abridged.tsv")
        or name.endswith(".fusioninspector.fusions.abridged.filtered.tsv")
        or name.endswith(".fusioninspector.fusions.filtered.tsv")
        # Uncomment to accept unfiltered outputs
        # or name.endswith(".fusioninspector.fusions.abridged.tsv")
        # or name.endswith(".fusioninspector.fusions.tsv")
        # or name.endswith(".fusioninspector.tsv")
    )

def discover_fusioninspector_files(input_paths, recursive=False):
    """
    Discover FusionInspector TSV files.
    input_paths : str, Path, or iterable
        One or more files/directories.
    recursive : bool
        Recursively search supplied directories.
    Returns
    list[str]
        Sorted unique FusionInspector TSV files.
    """

    if not input_paths:
        return []

    # Allow single path or list of paths
    if isinstance(input_paths, (str, Path)):
        input_paths = [input_paths]

    discovered = []

    for input_path in input_paths:

        expanded_paths = glob.glob(str(input_path), recursive=recursive)

        if not expanded_paths:
            expanded_paths = [str(input_path)]

        for expanded in expanded_paths:

            path = Path(expanded)

            if not path.exists():
                logger.warning("Input path does not exist: %s", path)
                continue

            if path.is_file():

                if fusioninspector_input_matches(path):
                    discovered.append(str(path.resolve()))

                continue

            search_iter = path.rglob("*") if recursive else path.iterdir()

            for candidate in search_iter:

                if candidate.is_file() and fusioninspector_input_matches(candidate):
                    discovered.append(str(candidate.resolve()))

    discovered = sorted(set(discovered))

    logger.info(
        "Discovered %d FusionInspector TSV file(s).",
        len(discovered),
    )

    return discovered

def derive_sample_label(file_path):
    """Derive a sample identifier from a FusionInspector output filename."""

    path = Path(file_path)
    stem = path.name

    # Remove optional compression extension.
    stem = re.sub(r"(?i)\.(?:gz|bgz|bz2)$", "", stem)

    # Remove table extension.
    stem = re.sub(r"(?i)\.(?:tsv|txt|csv)$", "", stem)

    # Remove supported FusionInspector suffixes.
    stem = re.sub(
        r"(?i)\.fusioninspector\.fusions(?:\.abridged)?$",
        "",
        stem,
    )

    # Remove common RNA-seq sample suffixes such as -T or _T.
    stem = re.sub(
        r"(?i)(?:[._-](?:T|N|tumor|normal))+$",
        "",
        stem,
    )

    stem = stem.strip("._-")

    if not stem:
        raise ValueError(
            f"Could not derive a sample identifier from FusionInspector file: {file_path}"
        )

    return stem

def infer_condition_from_sample(sample_id):
    """Infer case/control condition from sample label where possible."""
    text = str(sample_id or "").strip()
    token = text.upper()
    if token.startswith("CASE") or re.search(r"(^|[-_.])CASE($|[-_.])", token):
        return "case"
    if (
        token.startswith("CTRL")
        or token.startswith("CONTROL")
        or re.search(r"(^|[-_.])(CTRL|CONTROL)($|[-_.])", token)
    ):
        return "ctrl"
    return None

def group_fusioninspector_inputs(fusioninspector_paths=None, recursive=False):
    """Group discovered FusionInspector files by sample identifier."""

    groups = defaultdict(lambda: {"fusioninspector": []})

    files = discover_fusioninspector_files(
        fusioninspector_paths,
        recursive=recursive,
    )

    for file_path in files:
        sample_label = derive_sample_label(file_path)

        if sample_label.lower() == "fusioninspector":
            raise ValueError(
                "Invalid derived sample label 'fusioninspector' for file: "
                f"{file_path}"
            )

        groups[sample_label]["fusioninspector"].append(file_path)

        logger.debug(
            "Assigned FusionInspector file %s to sample %s",
            file_path,
            sample_label,
        )

    return dict(groups)

def load_and_parse_fusion_files(file_paths, parser_func, caller_name):
    """Load caller files; any unreadable input is fatal for release completeness."""
    dfs = []
    failures = []
    ledger = FailureLedger()
    for file_path in file_paths:
        ledger.record_attempt()
        try:
            df = pd.read_csv(file_path, sep="\t")
            parsed = parser_func(df)
            if not parsed.empty:
                parsed = deduplicate_fusions(parsed)
                parsed["source_file"] = str(file_path)
                parsed["source_basename"] = Path(file_path).name
                dfs.append(parsed)
                logger.info(
                    "Loaded %d fusions from %s: %s", len(parsed), caller_name, file_path
                )
            ledger.record_success()
        except (
            OSError,
            UnicodeError,
            pd.errors.ParserError,
            KeyError,
            ValueError,
        ) as e:
            logger.error("Failed to read %s file %s: %s", caller_name, file_path, e)
            failures.append((str(file_path), type(e).__name__, str(e)))
            ledger.record_failure(type(e).__name__)
    if failures:
        details = "; ".join(f"{path} [{kind}]: {message}" for path, kind, message in failures)
        raise RuntimeError(
            f"{len(failures)} {caller_name} input file(s) failed; refusing a partial release; "
            f"accounting={ledger.to_dict()}: {details}"
        )
    return dfs

def _worker_process_sample(payload):
    """Process one sample group inside a worker process."""
    sample_label, fusion_files, args = payload
    context = _WORKER_CONTEXT

    dfs = []
    dfs.extend(
        load_and_parse_fusion_files(
            fusion_files["fusioninspector"],
            parse_fusioninspector,
            "FusionInspector",
        )
    )

    if not dfs:
        return {
            "sample_results": {
                "protein_count": 0,
                "skipped_count": 0,
                "pair_evaluated_count": 0,
                "events_with_valid_output": 0,
                "skip_reasons": defaultdict(int),
            },
            "ranking_rows": [],
        }

    combined = pd.concat(dfs, ignore_index=True)
    combined = deduplicate_fusions(combined)

    sample_results = process_combined_fusions(
        combined=combined,
        sample_label=sample_label,
        resources=SampleProcessingContext(
            db=context.get("db"),
            genome=context.get("genome"),
            transcript_models=context.get("transcript_models"),
            transcript_alias_index=context.get("transcript_alias_index"),
            transcript_index=context.get("transcript_index"),
            gene_symbol_index=context.get("gene_symbol_index"),
            args=args,
            reference_peptides=context.get("ref_pep_set"),
            reference_proteins=context.get("ref_protein_set"),
        ),
    )

    return {
        "sample_results": sample_results,
        "ranking_rows": sample_results.get("ranking_rows", []),
    }

def _reopen_file_handles(args):
    """Fork initializer: replace inherited file-backed handles with worker-local ones.

    pyfaidx reads with seek()+read() on one file object; after fork, all workers
    would share the parent's file descriptor and therefore its file offset.
    SQLite connections must likewise not be carried across fork.
    """
    if Fasta is None:
        raise RuntimeError("pyfaidx is required for multi-worker fusion reconstruction")
    _WORKER_CONTEXT["genome"] = Fasta(args.genome, sequence_always_upper=True, rebuild=False)
    _WORKER_CONTEXT["db"] = FeatureDB(args.gtf_db, keep_order=True)

def _init_worker(args):
    """Spawn initializer: build all worker-local resources from scratch."""
    global _WORKER_CONTEXT
    # Imported lazily to avoid a circular import (fusion_pipeline imports this module).
    from .fusion_pipeline import load_reference_data, load_reference_proteome
    genome, db, models, aliases, transcript_index, symbol_index = load_reference_data(args)
    ref_proteins, ref_peptides = load_reference_proteome(args)
    _WORKER_CONTEXT = {
        "db": db,
        "genome": genome,
        "transcript_models": models,
        "transcript_alias_index": aliases,
        "transcript_index": transcript_index,
        "gene_symbol_index": symbol_index,
        "ref_pep_set": ref_peptides,
        "ref_protein_set": ref_proteins,
    }

def process_combined_fusions(
    combined: pd.DataFrame,
    sample_label: str,
    resources: SampleProcessingContext,
):
    """Reconstruct all valid fusion pairs for one combined sample table and return metadata rows."""
    args = resources.args
    stats = {
        "protein_count": 0,
        "skipped_count": 0,
        "pair_evaluated_count": 0,
        "events_with_valid_output": 0,
        "skip_reasons": defaultdict(int),
        "events_with_alternative_transcripts": 0,
        "alternative_isoform_pairs_not_evaluated": 0,
    }
    cds_cache = {}
    ranking_rows = []
    lookup = PartnerLookupContext(
        db=resources.db,
        genome=resources.genome,
        transcript_index=resources.transcript_index,
        transcript_alias_index=resources.transcript_alias_index,
        transcript_models=resources.transcript_models,
        gene_symbol_index=resources.gene_symbol_index,
        cds_cache=cds_cache,
        max_transcripts_per_gene=args.max_transcripts_per_gene,
    )
    references = ReferenceContext(
        genome=resources.genome,
        args=args,
        reference_peptides=resources.reference_peptides,
        reference_proteins=resources.reference_proteins,
    )

    for idx, row in combined.iterrows():
        context = parse_fusion_row_context(row)
        fusion_name = context["fusion_name"]

        log_fusion_progress(
            idx=idx,
            total=len(combined),
            sample_label=sample_label,
            fusion_name=fusion_name,
        )

        breakpoint1 = context["breakpoint1"]
        breakpoint2 = context["breakpoint2"]

        if not context["gene_1_symbol"] or not context["gene_2_symbol"]:
            record_skip(stats, "missing_normalized_gene_symbol")
            continue

        if breakpoint1 is None or breakpoint2 is None:
            record_skip(stats, "invalid_breakpoint_value")
            continue

        donor_candidates = collect_partner_candidates(
            lookup,
            PartnerRequest(
                gene_id=context["gene_1_id"],
                gene_symbol=context["gene_1_symbol"],
                preferred_transcript=context["preferred_tx1"],
                breakpoint_chrom=context["bp_chrom1"],
                breakpoint=breakpoint1,
            ),
        )

        acceptor_candidates = collect_partner_candidates(
            lookup,
            PartnerRequest(
                gene_id=context["gene_2_id"],
                gene_symbol=context["gene_2_symbol"],
                preferred_transcript=context["preferred_tx2"],
                breakpoint_chrom=context["bp_chrom2"],
                breakpoint=breakpoint2,
            ),
        )

        if not donor_candidates:
            logger.debug(
                "Skipping %s: no donor transcript with extractable CDS",
                fusion_name,
            )
            record_skip(stats, "donor_transcript_not_found_or_cds_failed")
            continue

        if not acceptor_candidates:
            logger.debug(
                "Skipping %s: no acceptor transcript with extractable CDS",
                fusion_name,
            )
            record_skip(stats, "acceptor_transcript_not_found_or_cds_failed")
            continue

        donor_total = donor_candidates[0].get("transcript_candidate_count", len(donor_candidates))
        acceptor_total = acceptor_candidates[0].get("transcript_candidate_count", len(acceptor_candidates))
        if donor_total > 1 or acceptor_total > 1:
            stats["events_with_alternative_transcripts"] += 1
        stats["alternative_isoform_pairs_not_evaluated"] += max(
            0, donor_total * acceptor_total - len(donor_candidates) * len(acceptor_candidates)
        )

        event_valid_count = 0

        for donor_idx, donor in enumerate(donor_candidates):
            for acceptor_idx, acceptor in enumerate(acceptor_candidates):
                stats["pair_evaluated_count"] += 1

                record, failure_reason = evaluate_candidate_pair(
                    CandidatePairRequest(
                        row=row,
                        sample_label=sample_label,
                        fusion_name=fusion_name,
                        event_index=idx,
                        donor_index=donor_idx,
                        acceptor_index=acceptor_idx,
                        donor=donor,
                        acceptor=acceptor,
                        breakpoint_chrom1=context["bp_chrom1"],
                        breakpoint_chrom2=context["bp_chrom2"],
                        breakpoint1=breakpoint1,
                        breakpoint2=breakpoint2,
                    ),
                    references,
                )

                if record is None:
                    record_skip(stats, failure_reason or "unknown")
                    continue

                ranking_rows.append(record)
                stats["protein_count"] += 1
                event_valid_count += 1

        if event_valid_count == 0:
            stats["skip_reasons"]["no_valid_isoform_pair"] += 1
            logger.debug(
                "Skipping %s: no donor/acceptor isoform pair yielded valid protein",
                fusion_name,
            )
        else:
            stats["events_with_valid_output"] += 1
            logger.debug(
                "Processed %s with %d valid isoform pair(s)",
                fusion_name,
                event_valid_count,
            )

    return {
        "input_fusion_count": len(combined),
        "protein_count": stats["protein_count"],
        "skipped_count": stats["skipped_count"],
        "pair_evaluated_count": stats["pair_evaluated_count"],
        "events_with_valid_output": stats["events_with_valid_output"],
        "skip_reasons": stats["skip_reasons"],
        "ranking_rows": ranking_rows,
        "events_with_alternative_transcripts": stats["events_with_alternative_transcripts"],
        "alternative_isoform_pairs_not_evaluated": stats["alternative_isoform_pairs_not_evaluated"],
    }

def process_samples(
    sample_groups,
    db,
    genome,
    transcript_models,
    transcript_alias_index,
    transcript_index,
    gene_symbol_index,
    args,
    ref_pep_set=None,
    ref_protein_set=None,
):
    """Process all FusionInspector sample groups and return rows plus summary statistics."""

    total_rows = 0
    ranking_rows = []
    protein_count = 0
    skipped_count = 0
    pair_evaluated_count = 0
    events_with_valid_output = 0
    events_with_alternative_transcripts = 0
    alternative_isoform_pairs_not_evaluated = 0
    skip_reasons = defaultdict(int)

    samples = sorted(sample_groups.items())

    if int(args.workers) > 1:
        # On POSIX, in-memory resources (transcript models, indices, reference
        # peptides) are inherited through fork, but file-backed pyfaidx/gffutils
        # handles are reopened in each worker by _reopen_file_handles. Spawn
        # platforms rebuild everything in _init_worker.
        global _WORKER_CONTEXT
        _WORKER_CONTEXT = {
            "db": db, "genome": genome, "transcript_models": transcript_models,
            "transcript_alias_index": transcript_alias_index,
            "transcript_index": transcript_index, "gene_symbol_index": gene_symbol_index,
            "ref_pep_set": ref_pep_set, "ref_protein_set": ref_protein_set,
        }
        pool_inputs = [
            (sample_label, fusion_files, args) for sample_label, fusion_files in samples
        ]

        available_methods = multiprocessing.get_all_start_methods()
        start_method = "fork" if "fork" in available_methods else "spawn"
        mp_context = multiprocessing.get_context(start_method)
        # Every worker must open its own genome/annotation handles. Sharing the
        # parent's pyfaidx file handle across forked processes shares one file
        # offset, so concurrent seek()+read() calls can return the wrong bases.
        initializer = _reopen_file_handles if start_method == "fork" else _init_worker
        initargs = (args,)

        with mp_context.Pool(
            processes=int(args.workers), initializer=initializer, initargs=initargs
        ) as pool:
            for res in pool.imap_unordered(_worker_process_sample, pool_inputs):
                sample_results = res.get("sample_results")
                ranking_rows_local = res.get("ranking_rows") or []

                if sample_results:
                    total_rows += sample_results.get("input_fusion_count", 0)
                    protein_count += sample_results.get("protein_count", 0)
                    skipped_count += sample_results.get("skipped_count", 0)
                    pair_evaluated_count += sample_results.get(
                        "pair_evaluated_count", 0
                    )
                    events_with_valid_output += sample_results.get(
                        "events_with_valid_output", 0
                    )
                    events_with_alternative_transcripts += sample_results.get("events_with_alternative_transcripts", 0)
                    alternative_isoform_pairs_not_evaluated += sample_results.get("alternative_isoform_pairs_not_evaluated", 0)

                    for reason, count in (
                        sample_results.get("skip_reasons") or {}
                    ).items():
                        skip_reasons[reason] += count

                ranking_rows.extend(ranking_rows_local)

    else:
        for sample_label, fusion_files in samples:
            logger.info("Processing sample %s", sample_label)

            dfs = []
            dfs.extend(
                load_and_parse_fusion_files(
                    fusion_files["fusioninspector"],
                    parse_fusioninspector,
                    "FusionInspector",
                )
            )

            if not dfs:
                logger.warning(
                    "No valid fusion caller data loaded for sample %s",
                    sample_label,
                )
                continue

            combined = pd.concat(dfs, ignore_index=True)
            combined = deduplicate_fusions(combined)

            logger.info(
                "[%s] Total fusions after per-file deduplication: %d",
                sample_label,
                len(combined),
            )

            sample_results = process_combined_fusions(
                combined=combined,
                sample_label=sample_label,
                resources=SampleProcessingContext(
                    db=db,
                    genome=genome,
                    transcript_models=transcript_models,
                    transcript_alias_index=transcript_alias_index,
                    transcript_index=transcript_index,
                    gene_symbol_index=gene_symbol_index,
                    args=args,
                    reference_peptides=ref_pep_set,
                    reference_proteins=ref_protein_set,
                ),
            )

            total_rows += len(combined)
            protein_count += sample_results["protein_count"]
            skipped_count += sample_results["skipped_count"]
            pair_evaluated_count += sample_results["pair_evaluated_count"]
            events_with_valid_output += sample_results["events_with_valid_output"]
            events_with_alternative_transcripts += sample_results["events_with_alternative_transcripts"]
            alternative_isoform_pairs_not_evaluated += sample_results["alternative_isoform_pairs_not_evaluated"]

            for reason, count in sample_results["skip_reasons"].items():
                skip_reasons[reason] += count

            ranking_rows.extend(sample_results["ranking_rows"])

    summary = {
        "total_rows": total_rows,
        "protein_count": protein_count,
        "skipped_count": skipped_count,
        "pair_evaluated_count": pair_evaluated_count,
        "events_with_valid_output": events_with_valid_output,
        "skip_reasons": skip_reasons,
        "events_with_alternative_transcripts": events_with_alternative_transcripts,
        "alternative_isoform_pairs_not_evaluated": alternative_isoform_pairs_not_evaluated,
    }

    return ranking_rows, summary