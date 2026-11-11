#!/bin/bash
# Usage: 01a_extract_passing_rows.sh report.tsv outprefix
# for b in 1 2 3 4 5 6; do
#  bash 01a_extract_passing_rows.sh ../05_proteomic_search/02b_results_quantmsdiann_pgdb/pgdb_v5_batch$b/quant_tables/diann_report.tsv 01a_extract_passing_rows/v5_b$b
#done


report="$1"
out_prefix="$2"

cut -f1,4,15,16,18,19,20,22,23,45 "$report" |
  awk -F'\t' -v OFS='\t' -v cf="${out_prefix}.counts.txt" '
    NR == 1 { next }
    {
      n++
      if ($7 > 0.01) fg++
      if ($5 <= 0.01 && $7 <= 0.01 && $8 <= 0.01 && $9 <= 0.01) {
        p++
        print $1, $2, $3, $4, $10, $6
      }
    }
    END {
      print "rows", n > cf
      print "pass", p > cf
      print "fail_global", fg > cf
    }
  ' |
  gzip -1 > "${out_prefix}.pass.tsv.gz"
