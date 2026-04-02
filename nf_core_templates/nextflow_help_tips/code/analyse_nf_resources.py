import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import re
import numpy as np
import argparse

"""
This script analyzes Nextflow execution trace files to identify resource usage patterns and inefficiencies. It performs the following steps:
1. Recursively searches for execution_trace_* files in the specified input directory.
2. Cleans and standardizes resource usage data (CPU, memory, runtime).
3. Summarizes average resource usage by process.
4. Ranks processes by CPU and memory efficiency to identify over-allocations.
5. Generates a Nextflow config snippet with recommended resource overrides based on observed usage.
6. Creates visualizations of resource usage by process.
7. Outputs CSV files with detailed summaries and recommendations.
8. Prints a final summary of findings and generated files.

USAGE:
python analyse_resources.py -i /home/kcoetzer/nf/nf_results/quantms -p quantms_
"""
# ---------------------------------------------------
# 1. FIND TRACE FILES
# ---------------------------------------------------

parser = argparse.ArgumentParser(description="Analyze Nextflow trace resources.")
parser.add_argument(
    "-i",
    "--input-dir",
    default=".",
    help="Directory to recursively search for execution_trace_* files (default: current directory)",
)
parser.add_argument(
    "-p",
    "--output-prefix",
    default="",
    help="Prefix for generated output files, e.g. quantms_",
)
parser.add_argument(
    "--time-headroom",
    type=float,
    default=1.5,
    help="Multiplier applied to runtime estimate when generating Nextflow time (default: 1.5)",
)
parser.add_argument(
    "--time-quantile",
    type=float,
    default=0.9,
    help="Quantile of observed runtimes used for time recommendation (0-1, default: 0.9)",
)
parser.add_argument(
    "--min-time-minutes",
    type=int,
    default=10,
    help="Minimum time allocation in minutes for each process (default: 10)",
)
args = parser.parse_args()

input_dir = Path(args.input_dir).expanduser().resolve()
output_prefix = args.output_prefix
time_headroom = args.time_headroom
time_quantile = args.time_quantile
min_time_minutes = args.min_time_minutes

if not (0 < time_quantile <= 1):
    print("--time-quantile must be in the range (0, 1]")
    exit(1)

if time_headroom <= 0:
    print("--time-headroom must be > 0")
    exit(1)

if min_time_minutes <= 0:
    print("--min-time-minutes must be > 0")
    exit(1)

if not input_dir.exists() or not input_dir.is_dir():
    print(f"Input directory does not exist or is not a directory: {input_dir}")
    exit(1)

trace_files = list(input_dir.rglob("execution_trace_*"))

if not trace_files:
    print(f"No execution_trace_* files found in {input_dir}")
    exit()


def prefixed_output(name):
    return f"{output_prefix}{name}"

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

# Determine grouping column
group_col = None
for col in ["process", "name", "task"]:
    if col in df.columns:
        group_col = col
        break

if group_col is None:
    print("Error: No suitable grouping column (process/name/task) found")
    exit()

print(f"Grouping by: {group_col}")

# ---------------------------------------------------
# 2. CLEAN DATA
# ---------------------------------------------------
# mem_str is the string value from a memory column, e.g. "1 GB", "500 MB", "1024 KB", or just a number in bytes
def parse_memory(mem_str):
    """Convert memory string to bytes."""
    if pd.isna(mem_str):
        return None
    s = str(mem_str).strip()
    if not s:
        return None

    m = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*([KMGT]?)(?:i?B)?\s*$", s, flags=re.IGNORECASE)
    if not m:
        return None

    value = float(m.group(1))
    unit = m.group(2).upper()
    multipliers = {
        "": 1,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
        "T": 1024**4,
    }
    return value * multipliers.get(unit, 1)

# Clean %cpu column (remove % signs and duplicates, convert to numeric)
if "%cpu" in df.columns:
    # Extract first numeric value from strings like '190.1%' or '190.1%190.1%'
    df["%cpu"] = df["%cpu"].astype(str).str.split('%').str[0]
    df["%cpu"] = pd.to_numeric(df["%cpu"], errors='coerce')
if "cpus" in df.columns:
    df["cpus"] = pd.to_numeric(df["cpus"], errors="coerce")

if "%cpu" in df.columns and "cpus" in df.columns:
    df["cpu_efficiency"] = df["%cpu"] / (df["cpus"] * 100)

if "memory" in df.columns:
    df["memory_bytes"] = df["memory"].apply(parse_memory)

if "rss" in df.columns:
    df["rss_bytes"] = df["rss"].apply(parse_memory)

if "memory_bytes" in df.columns and "rss_bytes" in df.columns:
    df["mem_efficiency"] = df["rss_bytes"] / df["memory_bytes"]

# Clean duration columns
if "duration" in df.columns:
    df["duration_sec"] = pd.to_timedelta(df["duration"], errors='coerce').dt.total_seconds()

if "realtime" in df.columns:
    df["realtime_sec"] = pd.to_timedelta(df["realtime"], errors='coerce').dt.total_seconds()

runtime_candidates = [col for col in ["duration_sec", "realtime_sec"] if col in df.columns]
if runtime_candidates:
    # Use the larger observed runtime when both columns exist to avoid underestimation.
    df["runtime_sec"] = df[runtime_candidates].max(axis=1)

if "peak_rss" in df.columns:
    df["peak_rss_bytes"] = df["peak_rss"].apply(parse_memory)

# //TODO Add peak_vmem column ?
#if "peak_vmem" in df.columns:
#    df["peak_vmem_bytes"] = df["peak_vmem"].apply(parse_memory)

# ---------------------------------------------------
# 3. PROCESS SUMMARY
# ---------------------------------------------------

# Build aggregation dict based on available columns
agg_dict = {}
if "%cpu" in df.columns:
    agg_dict["%cpu"] = "mean"
if "duration_sec" in df.columns:
    agg_dict["duration_sec"] = "mean"
if "realtime_sec" in df.columns:
    agg_dict["realtime_sec"] = "mean"
if "peak_rss_bytes" in df.columns:
    agg_dict["peak_rss_bytes"] = "mean"
#if "peak_vmem_bytes" in df.columns:
#    agg_dict["peak_vmem_bytes"] = "mean"

if not agg_dict:
    print("No columns available for analysis")
    exit()

summary = df.groupby(group_col).agg(agg_dict)

# Convert memory back to GB for readability
if "peak_rss_bytes" in summary.columns:
    summary["peak_rss_GB"] = summary["peak_rss_bytes"] / (1024**3)
#if "peak_vmem_bytes" in summary.columns:
#    summary["peak_vmem_GB"] = summary["peak_vmem_bytes"] / (1024**3)

if "duration_sec" in summary.columns:
    summary = summary.sort_values("duration_sec", ascending=False)
elif "realtime_sec" in summary.columns:
    summary = summary.sort_values("realtime_sec", ascending=False)

detail_agg = {}
if "cpus" in df.columns:
    detail_agg["cpus"] = "mean"
if "%cpu" in df.columns:
    detail_agg["%cpu"] = "mean"
if "cpu_efficiency" in df.columns:
    detail_agg["cpu_efficiency"] = "mean"
if "duration_sec" in df.columns:
    detail_agg["duration_sec"] = "mean"

if detail_agg:
    detail_summary = df.groupby(group_col).agg(detail_agg)
    summary = summary.join(detail_summary, how="left", rsuffix="_detail")

if "cpu_efficiency" in summary.columns:
    summary["CPU_flag"] = summary["cpu_efficiency"].apply(
        lambda x: "OVERALLOCATED" if x < 0.4 else "OK"
)

if "cpu_efficiency" in summary.columns:
    summary["cpu_waste"] = 1 - summary["cpu_efficiency"]

summary.to_csv(prefixed_output("process_resource_summary.csv"))

print("\nTop slowest processes:")
print(summary.head(10))

# ---------------------------------------------------
# 4. CPU WASTE RANKING
# ---------------------------------------------------

if "cpu_waste" in summary.columns:
    cpu_waste = summary.sort_values("cpu_waste", ascending=False)

    if "%cpu" in cpu_waste.columns:
        # Recommend CPU request with 20% headroom above observed average usage.
        cpu_waste["ideal_cpus"] = (
            (cpu_waste["%cpu"] / 100) * 1.2
        ).apply(lambda x: max(1, int(np.ceil(x))) if pd.notna(x) else pd.NA)

    if "cpus" in cpu_waste.columns and "ideal_cpus" in cpu_waste.columns:
        cpu_waste["cpu_rightsize_delta"] = cpu_waste["ideal_cpus"] - cpu_waste["cpus"]

    cpu_waste.to_csv(prefixed_output("cpu_waste_ranking.csv"))
    print("\nWorst CPU efficiency:")
    print(cpu_waste.head(10))

# ---------------------------------------------------
# 5. MEMORY ANALYSIS
# ---------------------------------------------------

if "mem_efficiency" in df.columns:

    mem_summary = df.groupby(group_col).agg({
        "mem_efficiency": "mean",
        "memory_bytes": "mean",
        "rss_bytes": "mean"
    }).sort_values("mem_efficiency")

    mem_summary["memory_waste"] = 1 - mem_summary["mem_efficiency"]

    # Recommend memory request with 20% headroom above observed RSS usage.
    mem_summary["ideal_memory_GB"] = (mem_summary["rss_bytes"] * 1.2) / (1024**3)
    mem_summary["requested_memory_GB"] = mem_summary["memory_bytes"] / (1024**3)
    mem_summary["memory_rightsize_delta_GB"] = (
        mem_summary["ideal_memory_GB"] - mem_summary["requested_memory_GB"]
    )

    mem_summary.to_csv(prefixed_output("memory_waste_ranking.csv"))

    print("\nWorst memory efficiency:")
    print(mem_summary.head(10))


# ---------------------------------------------------
# 4. CPU USAGE RANKING
# ---------------------------------------------------

if "%cpu" in summary.columns:
    cpu_usage = summary.sort_values("%cpu", ascending=False)
    cpu_usage.to_csv(prefixed_output("cpu_usage_ranking.csv"))
    print("\nHighest CPU usage:")
    print(cpu_usage.head(10))

# ---------------------------------------------------
# 5. MEMORY ANALYSIS
# ---------------------------------------------------

if "peak_rss_GB" in summary.columns:
    mem_summary = summary.sort_values("peak_rss_GB", ascending=False)
    mem_summary.to_csv(prefixed_output("memory_usage_ranking.csv"))
    print("\nHighest memory usage:")
    print(mem_summary.head(10))

# ---------------------------------------------------
# 6. GENERATE NEXTFLOW PROCESS OVERRIDES
# ---------------------------------------------------

def format_duration_expression_for_nf(seconds):
    """Format seconds as a Nextflow duration expression with retry headroom."""
    if pd.isna(seconds) or seconds <= 0:
        return f"{min_time_minutes}.min"

    # Add configurable headroom to absorb run-to-run variance.
    padded_seconds = seconds * time_headroom

    # Ensure tiny tasks don't get unrealistically short limits like 1m.
    padded_seconds = max(padded_seconds, min_time_minutes * 60)

    if padded_seconds < 3600:
        # Round UP to nearest minute for durations < 1 hour.
        rounded_minutes = max(1, int(np.ceil(padded_seconds / 60)))
        return f"{rounded_minutes}.min"

    # Round UP to nearest hour for durations >= 1 hour.
    rounded_hours = max(1, int(np.ceil(padded_seconds / 3600)))
    return f"{rounded_hours}.hour"


process_overrides = pd.DataFrame(index=summary.index)

if "runtime_sec" in df.columns:
    runtime_recommendation = df.groupby(group_col)["runtime_sec"].quantile(time_quantile)
    process_overrides["runtime_recommendation_sec"] = runtime_recommendation

if "ideal_cpus" in locals().get("cpu_waste", pd.DataFrame()).columns:
    process_overrides["ideal_cpus"] = cpu_waste["ideal_cpus"]

if "ideal_memory_GB" in locals().get("mem_summary", pd.DataFrame()).columns:
    process_overrides["ideal_memory_GB"] = mem_summary["ideal_memory_GB"]

if "duration_sec_detail" in summary.columns:
    process_overrides["duration_sec_detail"] = summary["duration_sec_detail"]
elif "duration_sec" in summary.columns:
    process_overrides["duration_sec_detail"] = summary["duration_sec"]

if "ideal_cpus" not in process_overrides.columns and "cpus" in summary.columns:
    process_overrides["ideal_cpus"] = summary["cpus"].apply(
        lambda x: max(1, int(np.ceil(x))) if pd.notna(x) else pd.NA
    )

if "ideal_memory_GB" not in process_overrides.columns and "peak_rss_GB" in summary.columns:
    process_overrides["ideal_memory_GB"] = summary["peak_rss_GB"] * 1.2

config_lines = ["process {"]

for process_name, row in process_overrides.iterrows():
    if pd.isna(row.get("ideal_cpus")) and pd.isna(row.get("ideal_memory_GB")) and pd.isna(row.get("duration_sec_detail")):
        continue

    ideal_cpus = row.get("ideal_cpus")
    ideal_mem_gb = row.get("ideal_memory_GB")
    duration_val = row.get("runtime_recommendation_sec")
    if pd.isna(duration_val):
        duration_val = row.get("duration_sec_detail")
    time_expr = format_duration_expression_for_nf(duration_val)

    cpus_value = max(1, int(np.ceil(ideal_cpus))) if pd.notna(ideal_cpus) else 1
    memory_value = max(1, int(np.ceil(ideal_mem_gb))) if pd.notna(ideal_mem_gb) else 1

    config_lines.extend([
        f"    withName: '{process_name}' {{",
        f"        cpus   = {cpus_value}",
        f"        memory = {memory_value}.GB",
        f"        time = {{ {time_expr} * task.attempt }}",
        "        errorStrategy = { task.exitStatus in 137..140 ? 'retry' : 'terminate' }",
        "        maxRetries = 3",
        "    }",
    ])

config_lines.append("}")

with open(prefixed_output("process_resource_overrides.config"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(config_lines) + "\n")

# ---------------------------------------------------
# 7. PLOTS
# ---------------------------------------------------

plot_dir = Path(prefixed_output("resource_plots"))
plot_dir.mkdir(exist_ok=True)

# Runtime plot
if "duration_sec" in summary.columns:
    summary["duration_sec"].sort_values().plot(kind="barh", figsize=(10,8))
    plt.title("Process Runtime")
    plt.xlabel("Seconds")
    plt.tight_layout()
    plt.savefig(plot_dir / "runtime_by_process.png")
    plt.close()

# CPU usage plot
if "%cpu" in summary.columns:
    summary["%cpu"].sort_values().plot(kind="barh", figsize=(10,8))
    plt.title("CPU Usage by Process")
    plt.xlabel("% CPU")
    plt.tight_layout()
    plt.savefig(plot_dir / "cpu_usage.png")
    plt.close()

# Memory usage plot
if "peak_rss_GB" in summary.columns:
    summary["peak_rss_GB"].sort_values().plot(kind="barh", figsize=(10,8))
    plt.title("Peak Memory Usage by Process")
    plt.xlabel("GB")
    plt.tight_layout()
    plt.savefig(plot_dir / "memory_usage.png")
    plt.close()

print(f"\nPlots saved to {plot_dir}/")

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
print(f"- {prefixed_output('resource_plots')}/")
