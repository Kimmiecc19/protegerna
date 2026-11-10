#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# ---- Settings (override with environment variables) --------------------------
# Per-participant Sarek SV VCF folders (controlled access, not in the repository).
# Pass the folders as arguments, or set a glob here.
INPUT_DIR_GLOB="${INPUT_DIR_GLOB:-/path/to/sarek/part*/variant_calling}"
# Reheadered VCFs are written to $OUTPUT_DIR/fixed_vcf_names (not committed: participant data).
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/01a_fixed_vcf_names}"
# -------------------------------------------------------------------------------


mkdir -p "$OUTPUT_DIR"

sample_name_from_vcf() {
    local file="$1"
    # Everything before the caller token is the required cohort sample name.
    # Example:
    # CASE-NEUAB000NKC-00583.manta.diploid_sv_snpEff_VEP.ann.vcf
    # becomes CASE-NEUAB000NKC-00583.
    #basename "$file" | sed -E 's/\.(manta|tiddit)\..*$//'
    basename "$file" | sed -E 's/\.(germline)\..*$//'
}

# Accept explicit arguments, otherwise fall back to the built-in batch glob.
if [ "$#" -lt 1 ]; then
  mapfile -t input_dirs < <(compgen -G "$INPUT_DIR_GLOB" | sort)
else
  input_dirs=()
  for input_path in "$@"; do
    if [ -d "$input_path" ]; then
      input_dirs+=( "$input_path" )
    fi
  done
fi

if [ "${#input_dirs[@]}" -eq 0 ]; then
  echo "ERROR: No input directories found"
  echo "Expected directories matching: $INPUT_DIR_GLOB"
  exit 1
fi

vcf_inputs=()
for input_dir in "${input_dirs[@]}"; do
  while IFS= read -r -d '' vcf_file; do
    vcf_inputs+=( "$vcf_file" )
  done < <(find "$input_dir" -type f -name '*.vcf.gz' -print0 | sort -z)
done

# Create output directory for fixed VCFs
mkdir -p "$OUTPUT_DIR/fixed_vcf_names"

# 1. Fix sample names in VCFs  
# Reheader VCFs with proper sample names and save to fixed_survivor_vcf directory
echo "=== Fixing sample names in VCFs ==="
if [ "${#vcf_inputs[@]}" -eq 0 ]; then
  echo "No VCF files found"
  exit 1
fi

for vcf_file in "${vcf_inputs[@]}"; do
  sample_name=$(sample_name_from_vcf "$vcf_file")
  echo "Processing: $vcf_file → $sample_name"
  
  bcftools reheader -s <(echo "$sample_name") "$vcf_file" \
    -o "$OUTPUT_DIR/fixed_vcf_names/${sample_name}_fixed.vcf.gz"
done

# 2. Unzip VCFs in fixed_vcf_names directory for SURVIVOR input
echo ""
echo "=== Unzipping VCFs for SURVIVOR input ==="
vcf_count=$(ls "$OUTPUT_DIR"/fixed_vcf_names/*.vcf.gz 2>/dev/null | wc -l)
if [ "$vcf_count" -eq 0 ]; then
  echo "ERROR: No .vcf.gz files found in $OUTPUT_DIR/fixed_vcf_names/"
  ls -la "$OUTPUT_DIR/fixed_vcf_names/"
  exit 1
fi
echo "Found $vcf_count VCF files to process"

for gz_file in "$OUTPUT_DIR"/fixed_vcf_names/*.vcf.gz; do
  vcf_file="${gz_file%.vcf.gz}.vcf"
  echo "Unzipping: $gz_file → $vcf_file"
  zcat "$gz_file" > "$vcf_file" || { echo "ERROR: Failed to unzip $gz_file"; exit 1; }
  if [ ! -s "$vcf_file" ]; then
    echo "ERROR: Output file $vcf_file is empty!"
    exit 1
  fi
done  

# 3. Create list of annotated VCFs for SURVIVOR merge with no path (SURVIVOR requires just filenames in the list)
echo ""
echo "=== Creating VCF list for SURVIVOR merge ==="
find "$OUTPUT_DIR/fixed_vcf_names" -maxdepth 1 -type f -name '*.vcf' | sort > "$OUTPUT_DIR/fixed_vcf_list.txt"
echo "VCF list created:"
cat "$OUTPUT_DIR/fixed_vcf_list.txt"

# OR GIVE FULL PATH? OR RUN FROM DATA DIRECTORY?
#ls fixed_vcf_names/*.vcf > sv_vcf_list.txt
#echo "VCF list created:"
#cat sv_vcf_list.txt
