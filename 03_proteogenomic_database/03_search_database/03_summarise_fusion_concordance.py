"""Tabulate agreement between computational predictions, not experimental confirmation."""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


CATEGORIES = {
    "identical_protein": "Identical protein",
    "same_junction_peptide": "Same junction peptide",
    "frame_agreement": "Frame agreement",
    "discordant_sequence": "Discordant sequence",
    "no_caller_reference": "No caller reference",
}
FRAMES = ("INFRAME", "FRAMESHIFT")


def table(title, counts):
    frames = list(FRAMES)
    if any(frame not in FRAMES for _, frame in counts):
        frames.append("OTHER/UNKNOWN")
    labels = {"INFRAME": "In-frame", "FRAMESHIFT": "Frameshift"}
    lines = [title, "", "| Concordance category | " + " | ".join(
        labels.get(f, "Other/unknown") for f in frames) + " | Total |",
        "|---|" + "---:|" * (len(frames) + 1)]
    categories = list(CATEGORIES) + sorted({c for c, _ in counts} - CATEGORIES.keys())
    totals = [0] * len(frames)
    for category in categories:
        values = [counts[category, frame] for frame in frames]
        totals = [a + b for a, b in zip(totals, values)]
        lines.append("| " + CATEGORIES.get(category, category) + " | " +
                     " | ".join(f"{v:,}" for v in values + [sum(values)]) + " |")
    lines.append("| **Total** | " + " | ".join(
        f"**{v:,}**" for v in totals + [sum(totals)]) + " |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="fusion.biological.tsv")
    parser.add_argument("--output", type=Path, help="Optional Markdown output file")
    args = parser.parse_args()
    # Protein/CDS sequence fields can exceed csv's default field-size limit.
    csv.field_size_limit(100_000_000)
    all_counts, eligible_counts = Counter(), Counter()
    eligibility_values = {"true", "false", "1", "0", "yes", "no"}
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"caller_vs_reconstructed_concordance", "frame_status", "dia_fasta_include"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            parser.error("Missing columns: " + ", ".join(sorted(missing)))
        for line_number, row in enumerate(reader, 2):
            category = row["caller_vs_reconstructed_concordance"].strip() or "UNSPECIFIED"
            frame = row["frame_status"].strip().upper()
            frame = frame if frame in FRAMES else "OTHER/UNKNOWN"
            eligible = row["dia_fasta_include"].strip().lower()
            if eligible not in eligibility_values:
                parser.error(f"Invalid dia_fasta_include at line {line_number}: {eligible!r}")
            all_counts[category, frame] += 1
            if eligible in {"true", "1", "yes"}:
                eligible_counts[category, frame] += 1
    report = "\n\n".join([
        "Agreement between computational predictions; not experimental confirmation.",
        table("All reconstructed candidates", all_counts),
        table("DIA-eligible candidates (dia_fasta_include = true)", eligible_counts),
        "Counts represent candidate rows, not unique deduplicated database sequences. "
        "DIA eligibility describes the producer flag before final database deduplication.",
    ]) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)


if __name__ == "__main__":
    main()
