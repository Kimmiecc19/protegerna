import argparse
from pathlib import Path
import re

import numpy as np
import pandas as pd

"""
This script analyzes Nextflow execution trace files to identify resource usage patterns and inefficiencies. It performs the following steps:
1. Recursively searches for `execution_trace_*` files in the specified input directory.
2. Loads and cleans the data, parsing memory strings, durations, and CPU usage.
3. Summarizes resource usage by process, calculating mean CPU and memory usage, and efficiency metrics.
4. Ranks processes by CPU waste and memory waste, providing recommendations for right-sizing resources.
5. Generates a Nextflow config snippet with recommended resource overrides based on observed usage.
6. Outputs CSV summaries and generated resource override config.

USAGE:
python optimize_resources_17042026.py -i /home/kcoetzer/nf/nf_results/rnasplice -p rnasplice_

only tested with quantms and sarek with optimized configs.
"""


def validate_positive(name, value):
    """Ensure CLI numeric options are strictly positive."""
    if value <= 0:
        print(f"--{name} must be > 0")
        raise SystemExit(1)


def first_existing_column(columns, candidates):
    """Return the first matching column from candidates, else None."""
    return next((col for col in candidates if col in columns), None)


def build_mean_agg(columns, candidates):
    """Build a {'column': 'mean'} aggregation dict for available columns."""
    return {col: "mean" for col in candidates if col in columns}


def add_timedelta_seconds(df_in, source_col, target_col):
    """Parse a timedelta-like column to seconds when present."""
    if source_col in df_in.columns:
        df_in[target_col] = pd.to_timedelta(df_in[source_col], errors="coerce").dt.total_seconds()


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


def format_duration_expression_for_nf(seconds, time_headroom, min_time_minutes):
    """Format seconds as a Nextflow duration expression with retry headroom."""
    if pd.isna(seconds) or seconds <= 0:
        return f"{min_time_minutes}.min"

    padded_seconds = seconds * time_headroom
    padded_seconds = max(padded_seconds, min_time_minutes * 60)

    if padded_seconds < 3600:
        rounded_minutes = max(1, int(np.ceil(padded_seconds / 60)))
        return f"{rounded_minutes}.min"

    rounded_hours = max(1, int(np.ceil(padded_seconds / 3600)))
    return f"{rounded_hours}.hour"


def extract_task_name(name_str):
    """Extract task name without parameters in parentheses."""
    if pd.isna(name_str):
        return name_str
    s = str(name_str).strip()
    # Split on opening parenthesis and take the first part
    return s.split('(')[0].strip()


def prefixed_output(name, output_prefix):
    return f"{output_prefix}{name}"


def parse_args():
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
    return parser.parse_args()


def validate_and_resolve_inputs(args):
    input_dir = Path(args.input_dir).expanduser().resolve()

    if not (0 < args.time_quantile <= 1):
        print("--time-quantile must be in the range (0, 1]")
        raise SystemExit(1)

    validate_positive("time-headroom", args.time_headroom)
    validate_positive("min-time-minutes", args.min_time_minutes)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist or is not a directory: {input_dir}")
        raise SystemExit(1)

    return input_dir


def load_trace_dataframe(input_dir):
    trace_files = list(input_dir.rglob("execution_trace_*"))
    if not trace_files:
        print(f"No execution_trace_* files found in {input_dir}")
        raise SystemExit(0)

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
        except Exception as exc:
            print(f"Skipping {file}: {exc}")

    if not dfs:
        print("No non-empty execution_trace_* files with usable data found")
        raise SystemExit(0)

    df = pd.concat(dfs, ignore_index=True)

    print(f"Loaded {len(trace_files)} trace files")
    print(f"Total tasks analyzed: {len(df)}")
    print(f"Available columns: {', '.join(df.columns)}")

    return df


def clean_data(df):
    if "%cpu" in df.columns:
        # Extract first numeric value from strings like '190.1%' or '190.1%190.1%'
        df["%cpu"] = df["%cpu"].astype(str).str.split("%").str[0]
        df["%cpu"] = pd.to_numeric(df["%cpu"], errors="coerce")

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

    add_timedelta_seconds(df, "duration", "duration_sec")
    add_timedelta_seconds(df, "realtime", "realtime_sec")

    runtime_candidates = [col for col in ["duration_sec", "realtime_sec"] if col in df.columns]
    if runtime_candidates:
        # Use the larger observed runtime when both columns exist to avoid underestimation.
        df["runtime_sec"] = df[runtime_candidates].max(axis=1)

    if "peak_rss" in df.columns:
        df["peak_rss_bytes"] = df["peak_rss"].apply(parse_memory)

    return df


def build_summary(df, group_col):
    agg_dict = build_mean_agg(df.columns, ["%cpu", "duration_sec", "realtime_sec", "peak_rss_bytes"])
    if not agg_dict:
        print("No columns available for analysis")
        raise SystemExit(0)

    summary = df.groupby(group_col).agg(agg_dict)

    if "peak_rss_bytes" in summary.columns:
        summary["peak_rss_GB"] = summary["peak_rss_bytes"] / (1024**3)

    if "duration_sec" in summary.columns:
        summary = summary.sort_values("duration_sec", ascending=False)
    elif "realtime_sec" in summary.columns:
        summary = summary.sort_values("realtime_sec", ascending=False)

    detail_agg = build_mean_agg(df.columns, ["cpus", "%cpu", "cpu_efficiency", "duration_sec"])
    if detail_agg:
        detail_summary = df.groupby(group_col).agg(detail_agg)
        summary = summary.join(detail_summary, how="left", rsuffix="_detail")

    if "cpu_efficiency" in summary.columns:
        summary["CPU_flag"] = summary["cpu_efficiency"].apply(
            lambda x: "OVERALLOCATED" if x < 0.4 else "OK"
        )
        summary["cpu_waste"] = 1 - summary["cpu_efficiency"]

    print("\nTop slowest processes:")
    print(summary.head(10))

    return summary


def build_cpu_waste(summary, output_prefix):
    if "cpu_waste" not in summary.columns:
        return None

    cpu_waste = summary.sort_values("cpu_waste", ascending=False)

    if "%cpu" in cpu_waste.columns:
        # Recommend CPU request with 20% headroom above observed average usage.
        cpu_waste["ideal_cpus"] = ((cpu_waste["%cpu"] / 100) * 1.2).apply(
            lambda x: max(1, int(np.ceil(x))) if pd.notna(x) else pd.NA
        )

    if "cpus" in cpu_waste.columns and "ideal_cpus" in cpu_waste.columns:
        cpu_waste["cpu_rightsize_delta"] = cpu_waste["ideal_cpus"] - cpu_waste["cpus"]

    cpu_waste.to_csv(prefixed_output("cpu_waste_ranking.csv", output_prefix))
    print("\nWorst CPU efficiency:")
    print(cpu_waste.head(10))

    return cpu_waste


def build_memory_waste(df, group_col, output_prefix):
    if "mem_efficiency" not in df.columns:
        return None

    mem_waste_summary = (
        df.groupby(group_col)
        .agg({"mem_efficiency": "mean", "memory_bytes": "mean", "rss_bytes": "mean"})
        .sort_values("mem_efficiency")
    )

    mem_waste_summary["memory_waste"] = 1 - mem_waste_summary["mem_efficiency"]

    # Recommend memory request with 20% headroom above observed RSS usage.
    mem_waste_summary["ideal_memory_GB"] = (mem_waste_summary["rss_bytes"] * 1.2) / (1024**3)
    mem_waste_summary["requested_memory_GB"] = mem_waste_summary["memory_bytes"] / (1024**3)
    mem_waste_summary["memory_rightsize_delta_GB"] = (
        mem_waste_summary["ideal_memory_GB"] - mem_waste_summary["requested_memory_GB"]
    )

    mem_waste_summary.to_csv(prefixed_output("memory_waste_ranking.csv", output_prefix))

    print("\nWorst memory efficiency:")
    print(mem_waste_summary.head(10))

    return mem_waste_summary


def build_process_overrides(df, summary, group_col, time_quantile, cpu_waste, mem_waste_summary):
    process_overrides = pd.DataFrame(index=summary.index)

    if "runtime_sec" in df.columns:
        runtime_recommendation = df.groupby(group_col)["runtime_sec"].quantile(time_quantile)
        process_overrides["runtime_recommendation_sec"] = runtime_recommendation

    if cpu_waste is not None and "ideal_cpus" in cpu_waste.columns:
        process_overrides["ideal_cpus"] = cpu_waste["ideal_cpus"]

    if mem_waste_summary is not None and "ideal_memory_GB" in mem_waste_summary.columns:
        process_overrides["ideal_memory_GB"] = mem_waste_summary["ideal_memory_GB"]

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

    return process_overrides


def write_overrides_config(process_overrides, output_prefix, time_headroom, min_time_minutes):
    config_lines = ["process {"]

    for process_name, row in process_overrides.iterrows():
        if (
            pd.isna(row.get("ideal_cpus"))
            and pd.isna(row.get("ideal_memory_GB"))
            and pd.isna(row.get("duration_sec_detail"))
        ):
            continue

        ideal_cpus = row.get("ideal_cpus")
        ideal_mem_gb = row.get("ideal_memory_GB")
        duration_val = row.get("runtime_recommendation_sec")
        if pd.isna(duration_val):
            duration_val = row.get("duration_sec_detail")

        time_expr = format_duration_expression_for_nf(duration_val, time_headroom, min_time_minutes)

        cpus_value = max(1, int(np.ceil(ideal_cpus))) if pd.notna(ideal_cpus) else 1
        memory_value = max(1, int(np.ceil(ideal_mem_gb))) if pd.notna(ideal_mem_gb) else 1

        config_lines.extend(
            [
                f"    withName: '{process_name}' {{",
                f"        cpus   = {cpus_value}",
                f"        memory = {memory_value}.GB",
                f"        time = {{ {time_expr} * task.attempt }}",
                "        errorStrategy = 'retry'",
                "        maxRetries = 3",
                "    }",
            ]
        )

    config_lines.append("}")

    with open(prefixed_output("process_resource_overrides.config", output_prefix), "w", encoding="utf-8") as fh:
        fh.write("\n".join(config_lines) + "\n")


def main():
    args = parse_args()
    input_dir = validate_and_resolve_inputs(args)

    df = load_trace_dataframe(input_dir)
    group_col = first_existing_column(df.columns, ["process", "name", "task"])
    if group_col is None:
        print("Error: No suitable grouping column (process/name/task) found")
        raise SystemExit(1)

    print(f"Grouping by: {group_col}")

    # Extract task name without parameters in parentheses
    df[group_col] = df[group_col].apply(extract_task_name)

    df = clean_data(df)

    summary = build_summary(df, group_col)
    summary.to_csv(prefixed_output("process_resource_summary.csv", args.output_prefix))

    cpu_waste = build_cpu_waste(summary, args.output_prefix)
    mem_waste_summary = build_memory_waste(df, group_col, args.output_prefix)

    process_overrides = build_process_overrides(
        df,
        summary,
        group_col,
        args.time_quantile,
        cpu_waste,
        mem_waste_summary,
    )

    write_overrides_config(
        process_overrides,
        args.output_prefix,
        args.time_headroom,
        args.min_time_minutes,
    )

    print("\nFiles generated:")
    print(f"- {prefixed_output('process_resource_summary.csv', args.output_prefix)}")
    print(f"- {prefixed_output('process_resource_overrides.config', args.output_prefix)}")


if __name__ == "__main__":
    main()
