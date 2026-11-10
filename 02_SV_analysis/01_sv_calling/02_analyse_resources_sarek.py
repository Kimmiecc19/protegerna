"""Analyse Nextflow execution trace files for resource usage and inefficiencies.

1. Recursively finds `execution_trace_*` files in the input directory.
2. Parses memory strings, durations and CPU usage.
3. Summarises resource usage and efficiency per process.
4. Ranks processes by CPU/memory waste and usage, with right-sizing recommendations.
5. Writes CSV summaries and a Nextflow config snippet with recommended resource overrides.

USAGE:
python analyse_resources.py -i /home/kcoetzer/nf/nf_results/sarek -p sarek_
"""
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

GB = 1024**3
MEMORY_UNITS = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}

# ---------------------------------------------------
# 1. FIND TRACE FILES
# ---------------------------------------------------
parser = argparse.ArgumentParser(description="Analyze Nextflow trace resources.")
parser.add_argument("-i", "--input-dir", default=".",
                    help="Directory to recursively search for execution_trace_* files (default: current directory)")
parser.add_argument("-p", "--output-prefix", default="", help="Prefix for generated output files, e.g. quantms_")
parser.add_argument("--time-headroom", type=float, default=1.5,
                    help="Multiplier applied to runtime estimate when generating Nextflow time (default: 1.5)")
parser.add_argument("--time-quantile", type=float, default=0.9,
                    help="Quantile of observed runtimes used for time recommendation (0-1, default: 0.9)")
parser.add_argument("--min-time-minutes", type=int, default=10,
                    help="Minimum time allocation in minutes for each process (default: 10)")
args = parser.parse_args()

input_dir = Path(args.input_dir).expanduser().resolve()
output_prefix = args.output_prefix

for invalid, message in [
    (not 0 < args.time_quantile <= 1, "--time-quantile must be in the range (0, 1]"),
    (args.time_headroom <= 0, "--time-headroom must be > 0"),
    (args.min_time_minutes <= 0, "--min-time-minutes must be > 0"),
    (not input_dir.is_dir(), f"Input directory does not exist or is not a directory: {input_dir}"),
]:
    if invalid:
        print(message)
        exit(1)

trace_files = list(input_dir.rglob("execution_trace_*"))
if not trace_files:
    print(f"No execution_trace_* files found in {input_dir}")
    exit()


def prefixed_output(name):
    return f"{output_prefix}{name}"


def save_and_print_top(df_in, sort_col, ascending, output_name, heading, top_n=10):
    """Sort a dataframe, save to CSV, and print top rows."""
    ranked = df_in.sort_values(sort_col, ascending=ascending)
    ranked.to_csv(prefixed_output(output_name))
    print(f"\n{heading}:")
    print(ranked.head(top_n))
    return ranked


def ceil_at_least_one(value):
    return max(1, int(np.ceil(value)))


dfs = []
for file in trace_files:
    try:
        trace_df = pd.read_csv(file, sep="\t")
        if trace_df.empty:
            continue
        trace_df = trace_df.dropna(axis=1, how="all")
        trace_df["source_file"] = str(file)
        trace_df["run"] = file.parent.name
        dfs.append(trace_df)
    except Exception as e:
        print(f"Skipping {file}: {e}")

if not dfs:
    print("No non-empty execution_trace_* files with usable data found")
    exit()

df = pd.concat(dfs, ignore_index=True)

print(f"Loaded {len(trace_files)} trace files")
print(f"Total tasks analyzed: {len(df)}")
print(f"Available columns: {', '.join(df.columns)}")

group_col = next((col for col in ["process", "name", "task"] if col in df.columns), None)
if group_col is None:
    print("Error: No suitable grouping column (process/name/task) found")
    exit()
print(f"Grouping by: {group_col}")


# ---------------------------------------------------
# 2. CLEAN DATA
# ---------------------------------------------------
def parse_memory(mem_str):
    """Convert a memory string such as "1 GB", "500 MB" or a plain byte count to bytes."""
    if pd.isna(mem_str):
        return None
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([KMGT]?)(?:i?B)?\s*$", str(mem_str).strip(), flags=re.IGNORECASE)
    return float(m.group(1)) * MEMORY_UNITS[m.group(2).upper()] if m else None


if "%cpu" in df.columns:
    # Keep the first value from strings like '190.1%' or '190.1%190.1%'.
    df["%cpu"] = pd.to_numeric(df["%cpu"].astype(str).str.split("%").str[0], errors="coerce")
if "cpus" in df.columns:
    df["cpus"] = pd.to_numeric(df["cpus"], errors="coerce")
if "%cpu" in df.columns and "cpus" in df.columns:
    df["cpu_efficiency"] = df["%cpu"] / (df["cpus"] * 100)

for column in ["memory", "rss"]:
    if column in df.columns:
        df[f"{column}_bytes"] = df[column].apply(parse_memory)
if "memory_bytes" in df.columns and "rss_bytes" in df.columns:
    df["mem_efficiency"] = df["rss_bytes"] / df["memory_bytes"]

for column in ["duration", "realtime"]:
    if column in df.columns:
        df[f"{column}_sec"] = pd.to_timedelta(df[column], errors="coerce").dt.total_seconds()
runtime_candidates = [col for col in ["duration_sec", "realtime_sec"] if col in df.columns]
if runtime_candidates:
    # Use the larger observed runtime when both columns exist to avoid underestimation.
    df["runtime_sec"] = df[runtime_candidates].max(axis=1)

if "peak_rss" in df.columns:
    df["peak_rss_bytes"] = df["peak_rss"].apply(parse_memory)

# ---------------------------------------------------
# 3. PROCESS SUMMARY
# ---------------------------------------------------
agg_dict = {col: "mean" for col in ["%cpu", "duration_sec", "realtime_sec", "peak_rss_bytes"] if col in df.columns}
if not agg_dict:
    print("No columns available for analysis")
    exit()

summary = df.groupby(group_col).agg(agg_dict)
if "peak_rss_bytes" in summary.columns:
    summary["peak_rss_GB"] = summary["peak_rss_bytes"] / GB
for col in ["duration_sec", "realtime_sec"]:
    if col in summary.columns:
        summary = summary.sort_values(col, ascending=False)
        break

detail_agg = {col: "mean" for col in ["cpus", "%cpu", "cpu_efficiency", "duration_sec"] if col in df.columns}
if detail_agg:
    summary = summary.join(df.groupby(group_col).agg(detail_agg), how="left", rsuffix="_detail")

if "cpu_efficiency" in summary.columns:
    summary["CPU_flag"] = summary["cpu_efficiency"].apply(lambda x: "OVERALLOCATED" if x < 0.4 else "OK")
    summary["cpu_waste"] = 1 - summary["cpu_efficiency"]

summary.to_csv(prefixed_output("process_resource_summary.csv"))
print("\nTop slowest processes:")
print(summary.head(10))

# ---------------------------------------------------
# 4. CPU WASTE RANKING
# ---------------------------------------------------
cpu_waste = None
if "cpu_waste" in summary.columns:
    cpu_waste = summary.copy()
    if "%cpu" in cpu_waste.columns:
        # Recommend CPU request with 20% headroom above observed average usage.
        cpu_waste["ideal_cpus"] = ((cpu_waste["%cpu"] / 100) * 1.2).apply(
            lambda x: ceil_at_least_one(x) if pd.notna(x) else pd.NA)
        if "cpus" in cpu_waste.columns:
            cpu_waste["cpu_rightsize_delta"] = cpu_waste["ideal_cpus"] - cpu_waste["cpus"]
    cpu_waste = save_and_print_top(cpu_waste, "cpu_waste", False, "cpu_waste_ranking.csv", "Worst CPU efficiency")

# ---------------------------------------------------
# 5. MEMORY WASTE RANKING
# ---------------------------------------------------
mem_waste_summary = None
if "mem_efficiency" in df.columns:
    mem_waste_summary = df.groupby(group_col).agg(
        {"mem_efficiency": "mean", "memory_bytes": "mean", "rss_bytes": "mean"})
    mem_waste_summary["memory_waste"] = 1 - mem_waste_summary["mem_efficiency"]
    # Recommend memory request with 20% headroom above observed RSS usage.
    mem_waste_summary["ideal_memory_GB"] = (mem_waste_summary["rss_bytes"] * 1.2) / GB
    mem_waste_summary["requested_memory_GB"] = mem_waste_summary["memory_bytes"] / GB
    mem_waste_summary["memory_rightsize_delta_GB"] = (
        mem_waste_summary["ideal_memory_GB"] - mem_waste_summary["requested_memory_GB"])
    mem_waste_summary = save_and_print_top(mem_waste_summary, "mem_efficiency", True,
                                           "memory_waste_ranking.csv", "Worst memory efficiency")

# ---------------------------------------------------
# 6. CPU AND MEMORY USAGE RANKINGS
# ---------------------------------------------------
if "%cpu" in summary.columns:
    save_and_print_top(summary, "%cpu", False, "cpu_usage_ranking.csv", "Highest CPU usage")
if "peak_rss_GB" in summary.columns:
    save_and_print_top(summary, "peak_rss_GB", False, "memory_usage_ranking.csv", "Highest memory usage")


# ---------------------------------------------------
# 7. GENERATE NEXTFLOW PROCESS OVERRIDES
# ---------------------------------------------------
def format_duration_expression_for_nf(seconds):
    """Format seconds as a Nextflow duration with headroom: minutes below one hour, else hours (rounded up)."""
    if pd.isna(seconds) or seconds <= 0:
        return f"{args.min_time_minutes}.min"
    padded_seconds = max(seconds * args.time_headroom, args.min_time_minutes * 60)
    if padded_seconds < 3600:
        return f"{ceil_at_least_one(padded_seconds / 60)}.min"
    return f"{ceil_at_least_one(padded_seconds / 3600)}.hour"


process_overrides = pd.DataFrame(index=summary.index)
if "runtime_sec" in df.columns:
    process_overrides["runtime_recommendation_sec"] = df.groupby(group_col)["runtime_sec"].quantile(args.time_quantile)
if cpu_waste is not None and "ideal_cpus" in cpu_waste.columns:
    process_overrides["ideal_cpus"] = cpu_waste["ideal_cpus"]
if mem_waste_summary is not None:
    process_overrides["ideal_memory_GB"] = mem_waste_summary["ideal_memory_GB"]
for col in ["duration_sec_detail", "duration_sec"]:
    if col in summary.columns:
        process_overrides["duration_sec_detail"] = summary[col]
        break
if "ideal_cpus" not in process_overrides.columns and "cpus" in summary.columns:
    process_overrides["ideal_cpus"] = summary["cpus"].apply(lambda x: ceil_at_least_one(x) if pd.notna(x) else pd.NA)
if "ideal_memory_GB" not in process_overrides.columns and "peak_rss_GB" in summary.columns:
    process_overrides["ideal_memory_GB"] = summary["peak_rss_GB"] * 1.2

config_lines = ["process {"]
for process_name, row in process_overrides.iterrows():
    ideal_cpus, ideal_mem_gb = row.get("ideal_cpus"), row.get("ideal_memory_GB")
    if pd.isna(ideal_cpus) and pd.isna(ideal_mem_gb) and pd.isna(row.get("duration_sec_detail")):
        continue
    duration_val = row.get("runtime_recommendation_sec")
    if pd.isna(duration_val):
        duration_val = row.get("duration_sec_detail")
    config_lines.extend([
        f"    withName: '{process_name}' {{",
        f"        cpus   = {ceil_at_least_one(ideal_cpus) if pd.notna(ideal_cpus) else 1}",
        f"        memory = {ceil_at_least_one(ideal_mem_gb) if pd.notna(ideal_mem_gb) else 1}.GB",
        f"        time = {{ {format_duration_expression_for_nf(duration_val)} * task.attempt }}",
        "        errorStrategy = 'retry'",
        "        maxRetries = 3",
        "    }",
    ])
config_lines.append("}")

with open(prefixed_output("process_resource_overrides.config"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(config_lines) + "\n")

# ---------------------------------------------------
# 8. FINAL SUMMARY
# ---------------------------------------------------
print("\nFiles generated:")
print(f"- {prefixed_output('process_resource_summary.csv')}")
if "%cpu" in summary.columns:
    print(f"- {prefixed_output('cpu_usage_ranking.csv')}")
if "peak_rss_GB" in summary.columns:
    print(f"- {prefixed_output('memory_usage_ranking.csv')}")
print(f"- {prefixed_output('process_resource_overrides.config')}")
