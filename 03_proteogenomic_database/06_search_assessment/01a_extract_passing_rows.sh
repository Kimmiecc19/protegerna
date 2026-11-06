#!/bin/bash
# usage: extract.sh report.tsv outprefix
cut -f1,4,15,16,18,19,20,22,23,45 "$1" | awk -F'\t' -v OFS='\t' -v cf="$2.counts.txt" 'NR==1{next} {n++; if($7>0.01) fg++; if($5<=0.01 && $7<=0.01 && $8<=0.01 && $9<=0.01){p++; print $1,$2,$3,$4,$10,$6}} END{print "rows",n > cf; print "pass",p > cf; print "fail_global",fg > cf}' | gzip -1 > "$2.pass.tsv.gz"
