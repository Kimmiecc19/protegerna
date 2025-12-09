# AnswerALS Proteomics

Created 14 August 2025

Peptides from iPSC-derived samples were analyzed on a 6600 TripleTOF mass spectrometer using **both DDA** (data-dependent acquisition) and **DIA/SWATH-MS** (data-independent acquisition).

* **DDA runs** were used to generate **sample-specific** and **cell-specific** peptide ion libraries by searching against the UniProt human proteome with iRT standards and decoy sequences. Data were processed through the Trans-Proteomic Pipeline (X!Tandem, Comet, PeptideProphet, iProphet) using a human canonical FASTA file (Uniprot) and refined into non-redundant consensus libraries with SpectraST. Retention times were mapped into iRT space, and assays were built from the top six most intense fragment ions.
* **DIA runs** (100 variable m/z windows) were matched against these libraries using OpenSWATH for peptide and protein quantification, with protein intensities calculated from summed proteotypic peptide transitions.
* **Differential expression** between ALS and control samples was calculated using mapDIA.
* Raw .wiff files were converted to profile-mode mzML (and in the DDA case, also mzXML) before processing.

* The search parameters included the following criteria: static modifications of Carbamidomethyl (C) and variable modifications of Oxidation (M). 
* The parent mass tolerance was set to be 50 p.p.m, and mono-isotopic fragment mass tolerance was 100 p.p.m (which was further filtered to be < 0.05 Da for building spectral library). 
* Tryptic peptides with up to three missed cleavages were allowed. 

---

### **1. Why they used DIA and DDA**

* **DDA (Data-Dependent Acquisition)**

  * Purpose: To **build the peptide ion libraries**.
  * In DDA, the mass spectrometer picks the most intense precursor ions for fragmentation, producing high-quality MS/MS spectra for peptide identification.
  * This is ideal for generating a **spectral reference library** — a catalog of peptides with their retention times, fragment ion patterns, and intensities.
  * They built:

    * **Sample-specific library** → made from the exact samples being studied, increasing identification accuracy.
    * **Cell-specific library** → likely built from DDA data of the same cell type (iPSC-derived cells in this case) to capture cell-type–specific proteins/peptides.

* **DIA (Data-Independent Acquisition / SWATH-MS)**

  * Purpose: To **quantify proteins across all samples** using the reference libraries.
  * In DIA, the instrument fragments *all* ions within fixed or variable m/z windows, giving comprehensive coverage and reproducible quantification — but the spectra are complex.
  * You then **deconvolute** these DIA spectra by matching them to the pre-built DDA libraries.

**Summary**: DDA = high-quality reference building, DIA = comprehensive quantification.

---

### **2. AnswerALS mzML file — is it DIA or DDA?**

From their methods (https://doi.org/10.1038/s41593-021-01006-0):

* **DDA raw files** (.wiff) were converted to mzML for library generation.
* **DIA (SWATH) raw files** (.wiff) were also converted to mzML for quantification.

So their mzML files **could be either** — it depends which part of the workflow they came from.
If they’re the final data for **quantification**, they are almost certainly **DIA mzML**.

---

### **3. How to check if an mzML is DIA or DDA**

1. **Look at isolation windows** in the mzML metadata:

   * **DDA** → narrow, variable precursor isolation widths (e.g., \~1–2 m/z) and *different* m/z for each MS/MS scan.
   * **DIA** → repeated wide/variable windows (e.g., 10–25 m/z) cycling across the full m/z range.
2. Tools:

   * `msconvert` (ProteoWizard) with `--filter "metadata"` to inspect headers.
   * `pyteomics` or `pymzml` in Python to print precursor isolation windows.

---

### **4. What are “sample-specific” and “cell-specific” libraries?**

* **Sample-specific library** → built from DDA runs of *the same* biological samples I will quantify in my analyses (participant samples). This captures:

  * Exact peptides present
  * Sample-specific sequence variants or PTMs (if detected)
  * Real retention times and intensities

* **Cell-specific library** → built from DDA data of *the same cell type*, but not necessarily the exact samples. Helps improve coverage if some peptides weren’t detected in your sample-specific library.

AnswerALS used both to:

* **Increase matching accuracy** in OpenSWATH
* Get better **statistical confidence** in peptide matches

---

### **5. How the libraries were used**

* DDA → Trans-Proteomic Pipeline (X!Tandem + Comet) → PeptideProphet → iProphet → SpectraST → output: consensus spectral library with decoys
* DIA → OpenSWATH searched against **DDA spectral libraries** → quantified transitions → protein-level intensities → statistical testing with mapDIA.

---

### **6. What to consider before using `nf-core/quantms`**

* **nf-core/quantms** expects **DIA** or **DDA-LFQ** mzML files plus a fasta protein database

TODO: Make sure you **use the same library** that was generated from the DDA runs if you want to reproduce their results.???

* If I only have the DIA mzMLs and no library, I can:

  * **Library-free DIA** (directDIA in DIA-NN or similar), but results may differ

TODO: Make sure mzMLs are **profile-mode** if OpenSWATH is part of the quantMS run — centroiding may affect results
TODO: Keep note of **variable SWATH window scheme** — the library must match it for correct extraction.

TODO: What else?

---

### Python script that inspects the **isolation window patterns** in an mzML file to make a best guess whether it’s **DIA** or **DDA**


Ensure that pyteomics is installed

```bash
pip install pyteomics
```

```python
#!/usr/bin/env python3

from pyteomics import mzml
import sys
import statistics

def check_dia_or_dda(mzml_file, num_scans_to_check=5000, dia_window_threshold=5):
    isolation_widths = []

    with mzml.MzML(mzml_file) as reader:
        count = 0
        for spectrum in reader:
            if spectrum.get('ms level') == 2:
                # Check precursor isolation window
                window_target = spectrum.get('precursorList', {}).get('precursor', [{}])[0].get('isolationWindow', {})
                lower_offset = window_target.get('isolation window lower offset')
                upper_offset = window_target.get('isolation window upper offset')

                if lower_offset and upper_offset:
                    width = float(lower_offset) + float(upper_offset)
                    isolation_widths.append(width)

                count += 1
                if count >= num_scans_to_check:
                    break

    if not isolation_widths:
        return "No MS2 isolation windows found. Cannot determine."

    # Statistics on isolation widths
    unique_widths = set(round(w, 2) for w in isolation_widths)
    avg_width = statistics.mean(isolation_widths)

    # DIA often has wider & repeated windows (e.g. 8–25 m/z) and few unique widths
    if avg_width > dia_window_threshold and len(unique_widths) < (len(isolation_widths) * 0.5):
        return f"DIA detected (avg isolation width ~{avg_width:.2f} m/z, {len(unique_widths)} unique widths)"
    else:
        return f"DDA detected (avg isolation width ~{avg_width:.2f} m/z, {len(unique_widths)} unique widths)"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} file.mzML")
        sys.exit(1)

    mzml_file = sys.argv[1]
    result = check_dia_or_dda(mzml_file)
    print(result)
```

---

#### **How the script works**

* Opens the mzML file.
* Reads the first few thousand MS2 scans.
* Calculates **isolation window width** for each scan.
* **DIA** → tends to have wide windows (e.g. 8–25 m/z) and *repeats the same widths*.
* **DDA** → narrow windows (e.g. 0.5–2 m/z) with *many different precursor m/z values*.
* Returns a guess plus stats on widths.

### Usage

```bash
python check_mzml_mode.py aals_file.mzML
```

---

## Batch-processing of mzML files to get DDA/DIA information

This script: 
* Scans a folder for **all `.mzML` files**
* Runs the DIA/DDA detection function
* Saves a **labeled PNG plot per file**
* Produces a CSV **summary** with acquisition type, average width, and number of unique widths

Install required packages

```bash
pip install pyteomics matplotlib pandas pathlib
```


```python
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

def plot_width_histogram(all_data, outpath):
    """
    Make a combined histogram of isolation window widths across all mzML files (log-scaled x-axis).
    TODO Add coloured grouping (overlaid) to see any differences between files/batches
    """
    plt.figure(figsize=(8, 5))
    
    # Combine all widths into one array
    all_widths = []
    for entry in all_data:
        all_widths.extend(entry["widths"])
    
    plt.hist(all_widths, bins=50, color="steelblue", edgecolor="black", alpha=0.7)
    
    plt.xscale("log")
    plt.xlabel("Isolation Window Width (m/z, log scale)")
    plt.ylabel("Count")
    plt.title("Combined Distribution of Isolation Window Widths (log scale)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
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
    parser.add_argument("--outdir", type=str, default="<directory>/mzML_mode_plots", help="Output directory for plots (default: <directory>/mzML_mode_plots)")
    parser.add_argument("--summary", type=str, default="<directory>/mzML_mode_summary.csv", help="Name of results summary (default: <directory>/mzML_mode_summary.csv)")
    parser.add_argument("--combined_plot", type=str, default="<directory>/combined_isolation_plot.png", help="Name of combined plot (default: <directory>/combined_isolation_plot.png)")
    parser.add_argument("--combined_histogram", type=str, default="<directory>/combined_histogram.png", help="Name of combined histogram (default: <directory>/combined_histogram.png)")
    parser.add_argument("--no-plot", action="store_true", help="Skip plotting (CSV only)")
    parser.add_argument("--max-scans", type=int, default=5000, help="Number of scans to check per file (default: 5000)")
    parser.add_argument("--dia-threshold", type=float, default=5.0, help="Isolation width threshold for DIA (default: 5.0)")
    args = parser.parse_args()

    directory = Path(args.directory)
    outdir = Path(args.outdir) if args.outdir else directory / summary
    outdir.mkdir(parents=True, exist_ok=True)

    """Exit script early if not files are found"""
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
    summary_csv = directory / args.summary
    pd.DataFrame(results).to_csv(summary_csv, index=False)
    print(f"\nSummary saved to: {summary_csv}")
    if not args.no_plot and all_data:
        combined_plot(all_data, outdir / args.combined_plot)
        plot_width_histogram(all_data, outdir / args.combined_histogram)
        print(f"Plots saved to: {outdir}")
# TODO: use tqdm to add progress bar? not necessary for nf-core
if __name__ == "__main__":
    main()
```

---

### Usage

```bash
python batch_mzml_mode_check.py \
directory /path/to/mzML_folder \
--outdir /path/to/output_folder \
--summary mzML_mode_summary.csv \
--combined_plot combined_isolation_plot.png \
--no-plot \
--max-scans 10000 \
--dia-threshold 5.0

python detect_mode_mzML.py --outdir batch_2/batch_2_mode --summary mzML_mode_summary_batch2.csv --combined_plot combined_plot_mode_batch2.png batch_2

python detect_mode_mzML_2.py --outdir test/test_mode --summary mzML_mode_summary_test.csv --combined_plot combined_plot_mode_test.png --combined_histogram combined_histogram_mode_test.png test
```

---

#### **How the script works**

1. DIA/DDA logic
* Opens the mzML file.
* Reads the first few thousand MS2 scans.
* Calculates **isolation window width** for each scan.
* **DIA** → tends to have wide windows (e.g. 8–25 m/z) and *repeats the same widths*.
* **DDA** → narrow windows (e.g. 0.5–2 m/z) with *many different precursor m/z values*.
* Returns a guess plus stats on widths.

2. Scatter plot of window widths
   * X-axis → scan number
   * Y-axis → isolation window center (m/z)
   * Color → window width (m/z)
3. In **DIA**, horizontal bands (repeated windows).
   In **DDA**, scattered points all over with varying centers and narrow widths.

---

### Expected Output

1. **CSV summary** (`mzML_mode_summary.csv`)

   | File         | Mode | Avg Isolation Width (m/z) | Unique Widths |
   | ------------ | ---- | ------------------------- | ------------- |
   | sample1.mzML | DIA  | 20.00                     | 30            |
   | sample2.mzML | DDA  | 1.20                      | 500           |

2. **Plots** in `mzML_mode_plots/` folder

   * DIA → horizontal stripes of repeated m/z windows
   * DDA → scattered narrow windows

---

TODO: If necessary - add a sorting step to automatically separate DIA and DDA files into subfolders** for easier use in nf-core/quantms

Combined plot is not helpful
Average out the values for each mzml and create the plot from the average (since they are all the same?)
Use a different plot?


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
    # Calculate average target m/z (window center)
    avg_target = np.mean(window_centers) if window_centers else float('nan')

    # DIA: wide, repeated windows; DDA: narrow, variable windows
    if avg_width > dia_window_threshold and len(unique_widths) < (len(isolation_widths) * 0.5):
        mode_guess = "DIA"
    else:
        mode_guess = "DDA"
    return mode_guess, avg_width, len(unique_widths), scan_numbers, window_centers, isolation_widths, avg_target


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
                    lower = target['isolation window lower offset']
                    upper = target['isolation window upper offset']
                    center = target['isolation window target m/z']
                    start = center - lower
                    end = center + upper
                    windows.append((start, end))
                except KeyError:
                    continue
            # Stop after collecting ~1 full cycle (20–40 windows typical for DIA)
            if len(windows) > 0 and len(set(windows)) > 15:
                break
    # Deduplicate and sort
    windows = sorted(set(windows), key=lambda x: x[0])
    return windows

def plot_swath_scheme(windows, out_path, title="SWATH Acquisition Scheme"):
    # TODO: label window widths on plot 
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (start, end) in enumerate(windows):
        ax.barh(y=0.5, width=end-start, left=start, height=0.3,
                align="center", edgecolor="black", alpha=0.7,
                label=f"Window {i+1}" if i < 10 else None)
    ax.set_xlabel("m/z")
    ax.set_yticks([])
    ax.set_title(title)
    if windows:
        ax.set_xlim(min(w[0] for w in windows)-10, max(w[1] for w in windows)+10)
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=300)
    plt.close()
    print(f"SWATH scheme saved: {out_path}")

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

def combined_plot(all_data, out_path):
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
    plt.savefig(out_path, dpi=300)
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
    swath_scheme_path = Path(args.swath_scheme) if args.swath_scheme else outdir / "swath_scheme.png"

    # Exit script early if no files are found
    mzml_files = collect_files(directory)
    if not mzml_files:
        print(f"No .mzML files found in {directory}")
        return

    results = []
    all_data = []
    for mzml_file in mzml_files:
        print(f"Processing {mzml_file}...")
        mode_guess, avg_width, num_unique, scans, centers, widths, avg_target = analyze_mzml(
            mzml_file, num_scans_to_check=args.max_scans, dia_window_threshold=args.dia_threshold)
        if mode_guess is None:
            print(f"  Skipped {mzml_file} (no MS2 isolation windows found)")
            continue
        results.append({
            "File": Path(mzml_file).name,
            "Mode": mode_guess,
            "Avg Isolation Width (m/z)": round(avg_width, 2),
            "Unique Widths": num_unique,
            "Average target": avg_target
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

    # Extract and plot combined SWATH scheme from all mzML files
    if mzml_files:
        all_windows = set()
        for mzml_file in mzml_files:
            windows = extract_windows(str(mzml_file))
            all_windows.update(windows)
        all_windows = sorted(all_windows, key=lambda x: x[0])
        print(f"Extracted {len(all_windows)} unique windows from {len(mzml_files)} files")
        for w in all_windows:
            print(f"  {w[0]:.1f} – {w[1]:.1f} m/z")
        if not args.no_plot:
            plot_swath_scheme(all_windows, swath_scheme_path, title=f"Combined SWATH Scheme ({len(mzml_files)} files)")

# TODO: use tqdm to add progress bar? not necessary for nf-core
if __name__ == "__main__":
    main()