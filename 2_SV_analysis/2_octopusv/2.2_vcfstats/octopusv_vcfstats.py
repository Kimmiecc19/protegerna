#!/usr/bin/env python3

"""
python vcfstats_29062026.py --vcf-dir /home/kcoetzer/objective_two/octopusv/octopusv_merged_02092026/merged --metadata sarek_metadata_stats_29062026.tsv --outprefix octopusv_merged

SV VCF statistics script for Manta/Tiddit/SURVIVOR/OctopuSV-style VCFs. It reports:
total and PASS SVs
SVTYPE counts
SV size bins
per-sample SV burden
genotype counts
case/control carrier counts if metadata is supplied
caller/source counts if SOURCE, SOURCES, or SUPP_VEC exist
"""

import argparse
import gzip
import glob
import re
from pathlib import Path
from collections import Counter
import pandas as pd


SIZE_BINS = [
    (50, 100, "50-100bp"),
    (100, 500, "100-500bp"),
    (500, 1000, "500bp-1kb"),
    (1000, 10000, "1-10kb"),
    (10000, 100000, "10-100kb"),
    (100000, 1000000, "100kb-1Mb"),
    (1000000, float("inf"), ">1Mb"),
]


def open_vcf(path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def parse_info(info_str):
    info = {}
    for item in info_str.split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            info[key] = value
        else:
            info[item] = True
    return info


def get_svlen(pos, info, ref, alt):
    if "SVLEN" in info:
        try:
            return abs(int(str(info["SVLEN"]).split(",")[0]))
        except ValueError:
            pass

    if "END" in info:
        try:
            return abs(int(info["END"]) - int(pos))
        except ValueError:
            pass

    if len(ref) != len(alt) and not alt.startswith("<"):
        return abs(len(ref) - len(alt))

    return None


def size_bin(svlen):
    if svlen is None:
        return "unknown"

    for lo, hi, label in SIZE_BINS:
        if lo <= svlen < hi:
            return label

    return "unknown"


def genotype_class(sample_field):
    if sample_field is None or sample_field in {".", "./.", ".|."}:
        return "missing"

    gt = sample_field.split(":")[0]

    if gt in {".", "./.", ".|."}:
        return "missing"

    alleles = re.split(r"[\/|]", gt)

    if any(a == "." for a in alleles):
        return "missing"

    if all(a == "0" for a in alleles):
        return "hom_ref"

    if all(a != "0" for a in alleles):
        return "hom_alt"

    return "het"


def is_carrier(sample_field):
    return genotype_class(sample_field) in {"het", "hom_alt"}


def normalise_condition(condition):
    condition = str(condition).strip().lower()

    if condition in {"case", "als", "patient", "affected"}:
        return "case"

    if condition in {"ctrl", "control", "healthy", "unaffected"}:
        return "control"

    return "unknown"


def read_metadata(path):
    if path is None:
        return {}

    meta = pd.read_csv(path, sep=None, engine="python")

    required = {"sample", "condition"}
    missing = required - set(meta.columns)

    if missing:
        raise ValueError(
            f"Metadata file must contain columns: sample, condition. "
            f"Missing: {', '.join(sorted(missing))}"
        )

    meta["condition"] = meta["condition"].map(normalise_condition)

    return dict(zip(meta["sample"].astype(str), meta["condition"].astype(str)))


def collect_vcf_files(args):
    vcf_files = []

    if args.vcf:
        vcf_files.append(args.vcf)

    if args.vcf_dir:
        for pattern in args.vcf_dir:
            for directory in glob.glob(pattern):
                directory = Path(directory)

                if not directory.exists():
                    continue

                if not directory.is_dir():
                    continue

                vcf_files.extend(directory.rglob("*.vcf"))
                vcf_files.extend(directory.rglob("*.vcf.gz"))

    vcf_files = sorted(set(str(v) for v in vcf_files))

    if not vcf_files:
        raise FileNotFoundError("No VCF files found.")

    return vcf_files


def parse_vcf_file(
    vcf,
    sample_to_condition,
    global_samples,
    summary_counts,
    svtype_counts,
    filter_counts,
    size_counts,
    caller_counts,
    genotype_counts,
    per_sample_burden,
    per_sample_type_burden,
    variant_rows,
):
    current_samples = []

    with open_vcf(vcf) as f:
        for line in f:
            line = line.rstrip("\n")

            if not line:
                continue

            if line.startswith("##"):
                continue

            if line.startswith("#CHROM"):
                header = line.split("\t")
                current_samples = header[9:]
                global_samples.update(current_samples)
                continue

            fields = line.split("\t")

            if len(fields) < 8:
                continue

            chrom, pos, var_id, ref, alt, qual, filt, info_str = fields[:8]
            sample_fields = fields[9:] if len(fields) > 9 else []

            info = parse_info(info_str)

            summary_counts["total_records"] += 1
            filter_counts[filt] += 1

            if filt == "PASS":
                summary_counts["pass_records"] += 1

            svtype = info.get("SVTYPE", "UNKNOWN")
            svlen = get_svlen(pos, info, ref, alt)
            svbin = size_bin(svlen)

            svtype_counts[svtype] += 1
            size_counts[svbin] += 1

            source = (
                info.get("SOURCE")
                or info.get("SOURCES")
                or info.get("CALLER")
                or info.get("CALLERS")
                or Path(vcf).name
            )

            for s in str(source).replace(",", ";").split(";"):
                s = s.strip()
                if s:
                    caller_counts[s] += 1

            case_carriers = 0
            control_carriers = 0
            unknown_carriers = 0
            total_carriers = 0

            for sample, sample_field in zip(current_samples, sample_fields):
                gt_cls = genotype_class(sample_field)
                genotype_counts[gt_cls] += 1

                if is_carrier(sample_field):
                    total_carriers += 1
                    per_sample_burden[sample] += 1
                    per_sample_type_burden[(sample, svtype)] += 1

                    condition = sample_to_condition.get(sample, "unknown")

                    if condition == "case":
                        case_carriers += 1
                    elif condition == "control":
                        control_carriers += 1
                    else:
                        unknown_carriers += 1

            variant_rows.append(
                {
                    "vcf_file": vcf,
                    "chrom": chrom,
                    "pos": int(pos),
                    "id": var_id,
                    "filter": filt,
                    "svtype": svtype,
                    "svlen": svlen,
                    "size_bin": svbin,
                    "source": source,
                    "total_carriers": total_carriers,
                    "case_carriers": case_carriers,
                    "control_carriers": control_carriers,
                    "unknown_carriers": unknown_carriers,
                }
            )


def write_counter(counter, columns, outpath, sort_by_count=True):
    df = pd.DataFrame(counter.items(), columns=columns)

    if not df.empty and sort_by_count:
        df = df.sort_values(columns[1], ascending=False)

    df.to_csv(outpath, sep="\t", index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Generate structural variant statistics from one VCF or recursively from VCF directories."
    )

    input_group = parser.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-v",
        "--vcf",
        help="Single VCF/VCF.gz file."
    )

    input_group.add_argument(
        "--vcf-dir",
        nargs="+",
        metavar="DIR",
        help="One or more directories containing VCF/VCF.gz files. Directories are searched recursively."
    )

    parser.add_argument(
        "-m",
        "--metadata",
        help="Optional TSV/CSV metadata file with columns: sample, condition."
    )

    parser.add_argument(
        "-o",
        "--outprefix",
        required=True,
        help="Output prefix."
    )

    args = parser.parse_args()

    sample_to_condition = read_metadata(args.metadata)
    vcf_files = collect_vcf_files(args)

    print(f"Found {len(vcf_files)} VCF file(s).")

    global_samples = set()
    summary_counts = Counter()

    svtype_counts = Counter()
    filter_counts = Counter()
    size_counts = Counter()
    caller_counts = Counter()
    genotype_counts = Counter()

    per_sample_burden = Counter()
    per_sample_type_burden = Counter()
    variant_rows = []

    for vcf in vcf_files:
        print(f"Processing: {vcf}")
        parse_vcf_file(
            vcf=vcf,
            sample_to_condition=sample_to_condition,
            global_samples=global_samples,
            summary_counts=summary_counts,
            svtype_counts=svtype_counts,
            filter_counts=filter_counts,
            size_counts=size_counts,
            caller_counts=caller_counts,
            genotype_counts=genotype_counts,
            per_sample_burden=per_sample_burden,
            per_sample_type_burden=per_sample_type_burden,
            variant_rows=variant_rows,
        )

    summary_df = pd.DataFrame(
        [
            {"metric": "total_records", "value": summary_counts["total_records"]},
            {"metric": "pass_records", "value": summary_counts["pass_records"]},
            {
                "metric": "nonpass_records",
                "value": summary_counts["total_records"] - summary_counts["pass_records"],
            },
            {"metric": "n_unique_samples_seen_in_vcfs", "value": len(global_samples)},
            {"metric": "n_vcf_files", "value": len(vcf_files)},
        ]
    )

    burden_df = pd.DataFrame(
        [
            {
                "sample": sample,
                "condition": sample_to_condition.get(sample, "unknown"),
                "sv_count": per_sample_burden.get(sample, 0),
            }
            for sample in sorted(global_samples)
        ]
    )

    burden_type_df = pd.DataFrame(
        [
            {
                "sample": sample,
                "condition": sample_to_condition.get(sample, "unknown"),
                "svtype": svtype,
                "sv_count": count,
            }
            for (sample, svtype), count in per_sample_type_burden.items()
        ]
    )

    variants_df = pd.DataFrame(variant_rows)

    summary_df.to_csv(f"{args.outprefix}.summary.tsv", sep="\t", index=False)

    write_counter(
        svtype_counts,
        ["svtype", "count"],
        f"{args.outprefix}.svtype_counts.tsv",
    )

    write_counter(
        filter_counts,
        ["filter", "count"],
        f"{args.outprefix}.filter_counts.tsv",
    )

    write_counter(
        size_counts,
        ["size_bin", "count"],
        f"{args.outprefix}.size_bins.tsv",
        sort_by_count=False,
    )

    write_counter(
        caller_counts,
        ["caller_or_source", "count"],
        f"{args.outprefix}.caller_source_counts.tsv",
    )

    write_counter(
        genotype_counts,
        ["genotype_class", "count"],
        f"{args.outprefix}.genotype_counts.tsv",
    )

    burden_df.to_csv(
        f"{args.outprefix}.per_sample_burden.tsv",
        sep="\t",
        index=False,
    )

    burden_type_df.to_csv(
        f"{args.outprefix}.per_sample_svtype_burden.tsv",
        sep="\t",
        index=False,
    )

    variants_df.to_csv(
        f"{args.outprefix}.variant_level_stats.tsv",
        sep="\t",
        index=False,
    )

    print(f"Done. Output prefix: {args.outprefix}")


if __name__ == "__main__":
    main()