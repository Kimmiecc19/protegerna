#!/bin/bash
# extract_scores.sh REPORT BATCH PEPTIDE_LIST OUT
# Writes DIA-NN score columns for (a) every row of the listed peptides and (b) a 1-in-150 systematic sample
# of all other rows as background. Columns kept: see header line written below.
awk -F'\t' -v OFS='\t' -v b="$2" -v list="$3" '
BEGIN{ while((getline l < list)>0){split(l,a,"\t"); if(a[1]!="peptide") want[a[1]]=1} }
NR==1{ print "batch","set","File.Name","Protein.Ids","Genes","Stripped.Sequence","Precursor.Id","Precursor.Charge","Q.Value","PEP","Global.Q.Value","PG.Q.Value","Global.PG.Q.Value","Precursor.Quantity","RT","Predicted.RT","Ms1.Profile.Corr","Evidence","Spectrum.Similarity","Mass.Evidence","CScore","Fragment.Quant.Corrected","Fragment.Correlations"; next }
{ s = ($15 in want) ? "listed" : ((NR % 150 == 0) ? "background" : "")
  if (s != "") print b,s,$1,$4,$6,$15,$16,$17,$18,$19,$20,$22,$23,$27,$33,$37,$42,$44,$45,$47,$48,$52,$53 }' "$1" > "$4"
