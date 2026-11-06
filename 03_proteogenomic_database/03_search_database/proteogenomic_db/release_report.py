"""Generate a caller-stratified final proteogenomic release audit."""
from __future__ import annotations
import argparse, csv, json
from collections import Counter, defaultdict
from pathlib import Path

def build_parser():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs",nargs="+",required=True,help="Producer/merge biological TSV files")
    parser.add_argument("--out_tsv",required=True); parser.add_argument("--out_json",required=True)
    return parser

def _truth(value): return str(value or "").strip().lower() in {"1","true","yes","y"}
def _caller(row,path): return str(row.get("source") or row.get("caller") or Path(path).stem.split(".")[0] or "unknown")
def _positive_number(value):
    try: return float(value or 0)>0
    except (TypeError,ValueError): return False

def summarize(paths):
    counters=defaultdict(Counter)
    for path in paths:
        with Path(path).open("r",encoding="utf-8-sig",newline="") as handle:
            for row in csv.DictReader(handle,delimiter="\t"):
                caller=_caller(row,path); counter=counters[caller]; counter["records"]+=1
                if _truth(row.get("transcript_selection_ambiguous")): counter["transcript_ambiguous"]+=1
                frame=str(row.get("frame_status") or "NA"); counter[f"frame:{frame}"]+=1
                if _truth(row.get("nmd_predicted")): counter["nmd_predicted"]+=1
                if _truth(row.get("has_reference_unique_tryptic_peptide")) or _truth(row.get("has_unique_junction_peptide")) or _positive_number(row.get("n_eligible_tryptic_peptides")): counter["peptide_evidence"]+=1
                reasons=str(row.get("exclusion_reason_codes") or row.get("fasta_exclusion_reasons") or row.get("dia_exclusion_reasons") or row.get("exclusion_reason") or "")
                for reason in filter(None,reasons.split(";")): counter[f"exclusion:{reason}"]+=1
    return {caller:dict(sorted(values.items())) for caller,values in sorted(counters.items())}

def main(argv=None):
    args=build_parser().parse_args(argv); summary=summarize(args.inputs)
    rows=[{"caller":caller,"metric":metric,"count":count} for caller,metrics in summary.items() for metric,count in metrics.items()]
    with Path(args.out_tsv).open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=["caller","metric","count"],delimiter="\t");writer.writeheader();writer.writerows(rows)
    Path(args.out_json).write_text(json.dumps({"schema_version":"pgdb-release-report-v1","callers":summary},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__":raise SystemExit(main())
