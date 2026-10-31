"""Validated, explainable, and resumable production-workflow facade."""
from __future__ import annotations
import argparse, difflib, hashlib, importlib, json, shlex, subprocess, sys, tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from proteogenomic.workflow_architecture import (
    STAGES_BY_SLUG, implementations_for, stage_for_implementation,
)

SOFTWARE_VERSION = "0.1.0"
STEP_MODULES = {"validate":"validate_gencode_translation","fusion":"fusiontoprotein","rmats":"rmatstoprotein","suppa":"suppatoprotein","benchmark":"benchmark_variant_reconstruction","merge":"merge_proteogenomic_database","qc":"proteogenomic_fasta_qc","report":"release_report"}
PARSERS = {"validate":("validate_gencode_translation","build_parser"),"fusion":("fusiontoprotein","build_parser"),"rmats":("proteogenomic.splice_cli","build_rmats_parser"),"suppa":("proteogenomic.splice_cli","build_suppa_parser"),"benchmark":("benchmark_variant_reconstruction","build_parser"),"merge":("merge_proteogenomic_database","build_parser"),"qc":("proteogenomic.qc_cli","build_parser"),"report":("release_report","build_parser")}
WORKFLOW_KEYS={"output_dir","resume"}
COMMON_KEYS={"gtf_db","genome","annotation_release","organism","reference_proteome","reference_peptide_cache","sample_metadata"}
STEP_COMMON={"validate":{"gtf_db","genome"},"fusion":COMMON_KEYS,"rmats":COMMON_KEYS-{"sample_metadata"},"suppa":COMMON_KEYS,"benchmark":set(),"merge":{"annotation_release","organism"},"qc":set(),"report":set()}
BOOLEAN_OPTIONAL={"fusion":{"exclude_incomplete_cds"},"rmats":{"exclude_incomplete_cds","require_ri_read_evidence","exclude_ri_nmd_from_primary","require_ri_junction_peptide"},"suppa":{"exclude_incomplete_cds"}}
INPUT_KEYS={"validate":{"gtf_db","genome","gencode_protein_fasta"},"fusion":{"fusioninspector","gtf_db","genome","sample_metadata","reference_proteome"},"rmats":{"gtf_db","genome","se_files","a3ss_files","a5ss_files","mxe_files","ri_files","reference_proteome"},"suppa":{"gtf_db","genome","event_files","psi_files","sample_metadata","reference_proteome"},"benchmark":{"actual","truth"},"merge":{"gencode_concordance_summary","inputs","reference_fasta","contaminants_fasta"},"qc":{"fasta","metadata","reference_proteome"},"report":{"inputs"}}
OUTPUT_KEYS={"validate":{"out_tsv","out_summary_json"},"fusion":{"biological_interpretation_tsv","filtered_cds_fasta","filtered_protein_fasta","dia_database_metadata_tsv"},"rmats":{"out_prot_fa","out_alt_start_prot_fa","out_exploratory_orf_fa","out_junc_fa","out_consequence_tsv","out_event_summary_tsv"},"suppa":{"out_prot_fa","out_alt_start_prot_fa","out_exploratory_orf_fa","out_junc_fa","out_consequence_tsv","out_psi_summary_tsv"},"benchmark":{"out_tsv","out_json"},"merge":{"out_fasta","out_metadata","out_mapping","out_peptide_evidence","out_biological_interpretation","out_summary_tsv","out_summary_json"},"qc":{"outdir"},"report":{"out_tsv","out_json"}}

def _parser_keys(step):
    module, factory=PARSERS[step]; parser=getattr(importlib.import_module(module),factory)()
    return {a.dest for a in parser._actions if a.dest not in {"help",argparse.SUPPRESS}}

def _unknown(section,key,choices):
    suggestion=difflib.get_close_matches(key,sorted(choices),n=1)
    prefix="Unknown top-level workflow section" if section=="root" else "Unknown workflow option"
    return ValueError(f"{prefix} [{section}].{key}"+(f"; did you mean '{suggestion[0]}'?" if suggestion else ""))

def validate_workflow(document):
    sections={"workflow","common",*STEP_MODULES}
    for section,value in document.items():
        if section not in sections: raise _unknown("root",section,sections)
        if not isinstance(value,Mapping): raise TypeError(f"Workflow section [{section}] must be a TOML table")
    for key in document.get("workflow",{}):
        if key not in WORKFLOW_KEYS: raise _unknown("workflow",key,WORKFLOW_KEYS)
    common=set().union(*STEP_COMMON.values())
    for key in document.get("common",{}):
        if key not in common: raise _unknown("common",key,common)
    for step in STEP_MODULES:
        allowed=_parser_keys(step)|{"enabled"}
        for key in document.get(step,{}):
            if key not in allowed: raise _unknown(step,key,allowed)

def load_workflow(path):
    with Path(path).open("rb") as handle: document=tomllib.load(handle)
    validate_workflow(document); return document

def _hash_json(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _hash_file(path):
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda:handle.read(1048576),b""): digest.update(block)
    return digest.hexdigest()

def _paths(values,keys):
    result=[]
    for key in keys:
        value=values.get(key); items=value if isinstance(value,list) else ([value] if value else [])
        for item in items:
            path=Path(str(item))
            if path.is_file(): result.append(path)
            elif path.is_dir(): result.extend(sorted(p for p in path.rglob("*") if p.is_file()))
    return list(dict.fromkeys(result))

OUTPUT_DEFAULTS={
 "validate":{"out_tsv":"gencode_translation_concordance.tsv","out_summary_json":"gencode_translation_concordance.json"},
 "fusion":{"filtered_protein_fasta":"fusion.primary.fasta","filtered_cds_fasta":"fusion.primary.cds.fasta","biological_interpretation_tsv":"fusion.biological.tsv","dia_database_metadata_tsv":"fusion.metadata.tsv"},
 "rmats":{"out_prot_fa":"rmats.primary.fasta","out_consequence_tsv":"rmats.consequences.tsv","out_event_summary_tsv":"rmats.events.tsv"},
 "suppa":{"out_prot_fa":"suppa.primary.fasta","out_consequence_tsv":"suppa.consequences.tsv","out_psi_summary_tsv":"suppa.psi.tsv"},
 "benchmark":{"out_tsv":"variant_reconstruction_benchmark.tsv","out_json":"variant_reconstruction_benchmark.json"},
 "merge":{"out_fasta":"proteogenomic_database.fasta","out_metadata":"proteogenomic_metadata.tsv","out_mapping":"proteogenomic_mapping.tsv","out_peptide_evidence":"proteogenomic_peptides.tsv","out_biological_interpretation":"proteogenomic_biological.tsv","out_summary_tsv":"proteogenomic_summary.tsv","out_summary_json":"proteogenomic_summary.json"},
 "qc":{"outdir":"qc"},"report":{"out_tsv":"release_report.tsv","out_json":"release_report.json"}}

def resolved_step(document,step):
    values={k:v for k,v in document.get("common",{}).items() if k in STEP_COMMON[step]}; values.update(document.get(step,{})); values.pop("enabled",None)
    out=document.get("workflow",{}).get("output_dir")
    if out:
        for key,name in OUTPUT_DEFAULTS[step].items(): values.setdefault(key,str(Path(out)/name))
    return values

def _tokens(name,value,optional=False):
    if value is None:return []
    if value is False:return ["--no-"+name] if optional else []
    if value is True:return ["--"+name]
    if isinstance(value,list):return ["--"+name,*map(str,value)]
    if isinstance(value,(str,int,float)):return ["--"+name,str(value)]
    raise TypeError(f"Unsupported value for option {name}: {type(value).__name__}")

def build_step_arguments(document,step):
    return [t for k,v in resolved_step(document,step).items() for t in _tokens(k,v,k in BOOLEAN_OPTIONAL.get(step,set()))]
def selected_steps(document,requested): return list(dict.fromkeys(requested)) if requested else [s for s in STEP_MODULES if document.get(s) and document[s].get("enabled",True)]

def explain(document,steps):
    for step in steps:
        configured={**{k:v for k,v in document.get("common",{}).items() if k in STEP_COMMON[step]},**document.get(step,{})}
        print(f"[{step}]")
        for key,value in sorted(resolved_step(document,step).items()):
            if key in configured: source="configuration"
            elif document.get("workflow",{}).get("output_dir") and key in OUTPUT_DEFAULTS[step]: source="output-directory convention"
            else: source="derived default"
            print(f"  {key} = {value!r}  # {source}")

def _manifest(step,values,config_hash):
    return {"schema_version":"pgdb-workflow-run-v1","software_version":SOFTWARE_VERSION,"step":step,"configuration_sha256":config_hash,"resolved_configuration":values,"input_sha256":{str(p):_hash_file(p) for p in _paths(values,INPUT_KEYS[step])}}
def _outputs_exist(step,values):
    paths=[Path(str(values[k])) for k in OUTPUT_KEYS[step] if values.get(k)]; return bool(paths) and all(p.exists() for p in paths)

def run_logged_command(command, log_path, *, stage, step, values, skip=False):
    """Stream combined child output to the terminal and an append-only stage log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        def record(message):
            log.write(message + "\n"); log.flush()
        record(f"\n=== {datetime.now(timezone.utc).isoformat()} ===")
        record(f"STAGE {stage.number}: {stage.name}; step={step}")
        record(f"Working directory: {Path.cwd()}")
        record(f"Command: {shlex.join(command)}")
        record("Resolved configuration: " + json.dumps(values, sort_keys=True, default=str))
        if skip:
            record("SKIPPED: configuration and input checksums match")
            return 0
        try:
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            ) as process:
                assert process.stdout is not None
                try:
                    for line in process.stdout:
                        log.write(line); log.flush()
                        sys.stdout.write(line); sys.stdout.flush()
                    returncode = process.wait()
                except BaseException:
                    process.terminate()
                    process.wait()
                    raise
        except BaseException as error:
            record(f"ABORTED: {type(error).__name__}: {error}")
            raise
        record(f"Finished: {datetime.now(timezone.utc).isoformat()}; exit_status={returncode}")
        return returncode

def build_parser():
    parser=argparse.ArgumentParser(description="Run the six-stage proteogenomic database workflow")
    parser.add_argument("config")
    parser.add_argument("--stage",action="append",choices=tuple(STAGES_BY_SLUG),default=[],help="Run one conceptual workflow stage (repeatable)")
    parser.add_argument("--step",action="append",choices=tuple(STEP_MODULES),default=[],help=argparse.SUPPRESS)
    parser.add_argument("--dry-run",action="store_true"); parser.add_argument("--explain",action="store_true"); parser.add_argument("--resume",action="store_true")
    return parser

def main(argv:Sequence[str]|None=None):
    raw=list(argv if argv is not None else sys.argv[1:]); explain_command=bool(raw and raw[0]=="explain")
    if explain_command:raw.pop(0)
    args=build_parser().parse_args(raw); document=load_workflow(args.config); settings=document.get("workflow",{})
    if args.stage:
        steps=[step for step in implementations_for(args.stage) if document.get(step) and document[step].get("enabled",True)]
    else:
        steps=selected_steps(document,args.step)
    if not steps:raise ValueError("No enabled workflow steps were configured")
    if explain_command or args.explain:explain(document,steps);return 0
    output_dir=settings.get("output_dir")
    if output_dir:Path(output_dir).mkdir(parents=True,exist_ok=True)
    for step in steps:
        stage=next((STAGES_BY_SLUG[slug] for slug in args.stage if step in STAGES_BY_SLUG[slug].implementations),stage_for_implementation(step))
        print(f"STAGE {stage.number}: {stage.name}", flush=True)
        values=resolved_step(document,step); config_hash=_hash_json({"step":step,"values":values}); manifest=_manifest(step,values,config_hash); state=Path(output_dir or ".")/".proteogenomic_state"/f"{step}.json"
        command=[sys.executable,"-u","-m",STEP_MODULES[step],*build_step_arguments(document,step)]
        log_path=Path(output_dir or ".")/"logs"/f"stage_{stage.number:02d}_{step}.log"
        if (args.resume or settings.get("resume")) and state.is_file() and _outputs_exist(step,values) and json.loads(state.read_text(encoding="utf-8"))==manifest:
            if not args.dry_run:
                run_logged_command(command,log_path,stage=stage,step=step,values=values,skip=True)
            print(f"SKIP {step}: configuration and input checksums match");continue
        print(shlex.join(command),flush=True)
        if args.dry_run:continue
        print(f"Log: {log_path}",flush=True)
        returncode=run_logged_command(command,log_path,stage=stage,step=step,values=values)
        if returncode:return returncode
        state.parent.mkdir(parents=True,exist_ok=True); state.write_text(json.dumps(manifest,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__":raise SystemExit(main())
