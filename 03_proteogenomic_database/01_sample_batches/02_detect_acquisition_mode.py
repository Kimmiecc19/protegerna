#!/usr/bin/env python3
"""
Batch mode detection of proteomic mass spectrometry mzML files (DIA or DDA) with plot and summary output.
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyteomics import mzml

def collect_files(directory):
    """Recursively collect all .mzML files in a directory."""
    return list(Path(directory).rglob("*.mzML"))

# TODO threshold is not necessary but I assume that DIA windows are wider than 5
def analyze_mzml(mzml_file, num_scans_to_check=5000, dia_window_threshold=5):
    """
    Analyze an mzML file to determine if it is DIA or DDA.
    Returns: (mode_guess, avg_width, num_unique_widths, scan_numbers, window_centers, isolation_widths)
    """
    isolation_widths = []
    window_centers = []
    scan_numbers = []
    try:
        # Read mzML with pyteomics - focusing on MS2 scans
        with mzml.MzML(str(mzml_file)) as reader:
            count = 0
            for spectrum in reader:
                if spectrum.get('ms level') == 2:
                    # For each MS2, extract isolation window information
                    precursor_info = spectrum.get('precursorList', {}).get('precursor', [{}])[0]
                    isolation_info = precursor_info.get('isolationWindow', {})
                    
                    lower_offset = isolation_info.get('isolation window lower offset')
                    upper_offset = isolation_info.get('isolation window upper offset')
                    target_mz = isolation_info.get('isolation window target m/z')
                    if lower_offset is not None and upper_offset is not None and target_mz is not None:
                        # # Calculate width of each isolation window by adding lower and upper offsets
                        width = float(lower_offset) + float(upper_offset)
                        isolation_widths.append(width)
                        window_centers.append(float(target_mz))
                        scan_numbers.append(count)
                    count += 1
                    if count >= num_scans_to_check:# # TODO: add intermediate file of width, window centers, for 500 scans
                        break
    except Exception as e:
        print(f"Error reading {mzml_file}: {e}")
        return None, None, None, None, None, None
    if not isolation_widths:
        return None, None, None, None, None, None

    #TODO what do unique widths have to do with it?
    # Calculate average width and unique widths
    rounded_widths = np.round(isolation_widths, 2)
    unique_widths = np.unique(rounded_widths)
    avg_width = np.mean(isolation_widths)

    # DIA: wide, repeated windows; DDA: narrow, variable windows
    # If average width is greater than threshold (5) and less than 50% unique widths, classify as DIA
    if avg_width > dia_window_threshold and len(unique_widths) < (len(isolation_widths) * 0.5):
        mode_guess = "DIA"
    else:
        mode_guess = "DDA"
    return mode_guess, avg_width, len(unique_widths), scan_numbers, window_centers, isolation_widths


def extract_windows(mzml_file):
    """
    Extract DIA isolation windows from the first complete cycle.
    Returns list of (lower, upper) window boundaries.
    """
    windows = []
    with mzml.MzML(mzml_file) as reader:
        for spec in reader:
            if spec['ms level'] == 2:
                try:
                    target = spec['precursorList']['precursor'][0]['isolationWindow']
                    lower_offset = target['isolation window lower offset']
                    upper = target['isolation window upper offset']
                    center = target['isolation window target m/z']
                    start = center - lower_offset
                    end = center + upper_offset
                    windows.append((start, end))
                except KeyError:
                    continue
            # Stop after collecting ~1 full cycle (20–40 windows typical for DIA)
            if len(windows) > 0 and len(set(windows)) > 15:
                break
    # Deduplicate and sort
    windows = sorted(set(windows), key=lambda x: x[0])
    return windows

def plot_swath_scheme(windows, out_png, title="SWATH Acquisition Scheme"):
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (start, end) in enumerate(windows):
        ax.barh(y=0.5, width=end-start, left=start, height=0.3,
                align="center", edgecolor="black", alpha=0.7,
                label=f"Window {i+1}" if i < 10 else None)  # only label first few
    ax.set_xlabel("m/z")
    ax.set_yticks([])
    ax.set_title(title)
    ax.set_xlim(min(w[0] for w in windows)-10, max(w[1] for w in windows)+10)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"SWATH scheme saved: {out_png}")

def plot_isolation_windows(scan_numbers, window_centers, isolation_widths, mzml_file, mode_guess, outdir):
    """Plot isolation window centers vs scan number, colored by width."""
    plt.figure(figsize=(10, 6))
    plt.scatter(scan_numbers, window_centers, c=isolation_widths, cmap='viridis', s=10)
    cbar = plt.colorbar()
    cbar.set_label('Isolation Window Width (m/z)')
    plt.xlabel("Scan Number")
    plt.ylabel("Isolation Window Center (m/z)")
    plt.title(f"{Path(mzml_file).name} | Mode: {mode_guess}")
    plt.tight_layout()
    out_path = Path(outdir) / (Path(mzml_file).name + ".png")
    plt.savefig(out_path, dpi=300)
    plt.close()

def combined_plot(all_data, output_path):
    """Plot all files together for comparison.
    TODO: combined plot is not very informative right now"""
    plt.figure(figsize=(12, 7))
    for entry in all_data:
        file_name = Path(entry["file"]).name
        scans = entry["scans"]
        centers = entry["centers"]
        widths = entry["widths"]
        mode = entry["mode"]
        plt.scatter(
            scans, centers,
            label=f"{file_name} ({mode}, mean width={np.mean(widths):.2f} m/z)",
            s=8, alpha=0.7
        )
    plt.xlabel("Scan Number")
    plt.ylabel("Isolation Window Center (m/z)")
    plt.title("DIA/DDA Isolation Window Comparison")
    plt.legend(fontsize=7, loc="best")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def main():
    """Argument parsing for user selection"""
    parser = argparse.ArgumentParser(description="Batch check mzML files for DIA or DDA mode.")
    parser.add_argument("directory", help="Directory containing mzML files")
    parser.add_argument("--outdir", type=str, default=None, help="Output directory for plots (default: <directory>/mzML_mode_plots)")
    parser.add_argument("--summary", type=str, default=None, help="Name of results summary (default: <directory>/mzML_mode_summary.csv)")
    parser.add_argument("--combined_plot", type=str, default=None, help="Name of combined plot (default: <directory>/combined_isolation_plot.png)")
    parser.add_argument("--swath_scheme", type=str, default=None, help="Output PNG file for SWATH scheme (default: <directory>/swath_scheme.png)")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting (CSV only)")
    parser.add_argument("--max-scans", type=int, default=5000, help="Number of scans to check per file (default: 5000)")
    parser.add_argument("--dia-threshold", type=float, default=5.0, help="Isolation width threshold for DIA (default: 5.0)")
    args = parser.parse_args()

    directory = Path(args.directory)
    outdir = Path(args.outdir) if args.outdir else directory / "mzML_mode_plots"
    outdir.mkdir(parents=True, exist_ok=True)

    summary_csv = Path(args.summary) if args.summary else directory / "mzML_mode_summary.csv"
    combined_plot_path = Path(args.combined_plot) if args.combined_plot else outdir / "combined_isolation_plot.png"
    swath_scheme_png = Path(args.swath_scheme) if args.swath_scheme else outdir / "swath_scheme.png"

    # Exit script early if no files are found
    mzml_files = collect_files(directory)
    if not mzml_files:
        print(f"No .mzML files found in {directory}")
        return

    results = []
    all_data = []
    for mzml_file in mzml_files:
        print(f"Processing {mzml_file}...")
        mode_guess, avg_width, num_unique, scans, centers, widths = analyze_mzml(
            mzml_file, num_scans_to_check=args.max_scans, dia_window_threshold=args.dia_threshold)
        if mode_guess is None:
            print(f"  Skipped {mzml_file} (no MS2 isolation windows found)")
            continue
        results.append({
            "File": Path(mzml_file).name,
            "Mode": mode_guess,
            "Avg Isolation Width (m/z)": round(avg_width, 2),
            "Unique Widths": num_unique,
            "Isolation Widths": widths,
            "Window Centers": centers
        })
        if not args.no_plot:
            plot_isolation_windows(scans, centers, widths, mzml_file, mode_guess, outdir)
        all_data.append({
            "file": str(mzml_file),
            "scans": scans,
            "centers": centers,
            "widths": widths,
            "mode": mode_guess
        })

    # Save summary CSV
    pd.DataFrame(results).to_csv(summary_csv, index=False)
    print(f"\nSummary saved to: {summary_csv}")
    if not args.no_plot and all_data:
        combined_plot(all_data, combined_plot_path)
        print(f"Plots saved to: {outdir}")

    # Only extract and plot SWATH scheme if at least one file is found
    if mzml_files:
        windows = extract_windows(str(mzml_files[0]))
        print(f"Extracted {len(windows)} windows from {mzml_files[0]}")
        for w in windows:
            print(f"  {w[0]:.1f} – {w[1]:.1f} m/z")
        if not args.no_plot:
            plot_swath_scheme(windows, swath_scheme_png, title=f"{mzml_files[0]} | SWATH Scheme")

# TODO: use tqdm to add progress bar? not necessary for nf-core
if __name__ == "__main__":
    main()