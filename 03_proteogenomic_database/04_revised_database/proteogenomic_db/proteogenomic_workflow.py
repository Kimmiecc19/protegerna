"""Validated, explainable, and resumable production-workflow facade."""
from __future__ import annotations
import argparse, difflib, hashlib, importlib, importlib.util, json, os, shlex, socket, subprocess, sys, tomllib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Mapping, Sequence
from proteogenomic.provenance import forget_file_hashes, resolve_input_files, sha256_file
from proteogenomic.workflow_architecture import (
    STAGES_BY_SLUG, implementations_for, stage_for_implementation,
)

SOFTWARE_VERSION = "0.1.0"
WORKFLOW_KEYS={"profile","output_dir","resume"}  # profile: legacy, only "publication"/"standard" accepted
COMMON_KEYS=frozenset({"gtf_db","genome","annotation_release","organism","reference_proteome","reference_peptide_cache","sample_metadata"})
QC_REPORTS=("sequence_qc","duplicate_sequences","qc_summary","length_distribution","header_metadata",
            "header_metadata_summary","quantms_validation","quantms_validation_summary")


def _derive_rescue_outputs(values):
    """Rescue tiers need their own FASTAs; derive conventional names when enabled."""
    if not values.get("out_prot_fa"): return
    stem=Path(str(values["out_prot_fa"])).with_suffix("")
    if values.get("allow_alt_start"): values.setdefault("out_alt_start_prot_fa",f"{stem}.alternative_start.fasta")
    if values.get("allow_longest_orf"): values.setdefault("out_exploratory_orf_fa",f"{stem}.exploratory_orf.fasta")


def _fusion_outputs(paths,values,get):
    """The digested-peptide table is only written when trypsin digestion is enabled."""
    if get("digest_trypsin") or not get("digested_peptide_tsv"): return paths
    return [p for p in paths if p!=Path(str(get("digested_peptide_tsv")))]


def _splice_outputs(paths,values,get):
    """The junction-peptide FASTA is only written with --short_junction_peptides."""
    if get("short_junction_peptides") or not get("out_junc_fa"): return paths
    return [p for p in paths if p!=Path(str(get("out_junc_fa")))]


def _suppa_outputs(paths,values,get):
    """The PSI filter summary is only written when PSI matrices are supplied."""
    paths=_splice_outputs(paths,values,get)
    if values.get("psi_files") or not get("out_psi_summary_tsv"): return paths
    return [p for p in paths if p!=Path(str(get("out_psi_summary_tsv")))]


def _qc_outputs(paths,values,get):
    """QC writes a fixed report set under outdir/prefix rather than one option per file."""
    out=Path(str(get("outdir"))); prefix=get("prefix"); names=list(QC_REPORTS)
    if values.get("metadata"): names.append("metadata_summary")
    if values.get("reference_proteome"): names.append("peptide_uniqueness")
    paths=paths+[out/f"{prefix}.{name}.tsv" for name in names]
    if get("write_filtered_fasta"):
        paths+=[out/f"{prefix}.filtered_min{get('min_protein_length')}aa.fasta",out/f"{prefix}.filtered_fasta_exclusions.tsv"]
    return paths


@dataclass(frozen=True)
class StepSpec:
    """Everything the runner needs to know about one workflow step, in one place.

    ``outputs`` maps each output option to its filename under ``[workflow].output_dir``
    (``None``: not defaulted from output_dir). Order is significant: it fixes the
    order of the generated command-line arguments.
    """
    module: str
    parser: tuple[str,str]
    common: frozenset[str]
    inputs: frozenset[str]
    outputs: Mapping[str,str|None]
    derive: Callable[[dict],None]|None=None
    extra_outputs: Callable|None=field(default=None)
    directory_outputs: frozenset[str]=frozenset()  # output options naming a directory, not a file
    # Sidecar suffixes whose files are fingerprinted with each input file because the
    # step reads them too (merge reads every producer's <FASTA>.run_config.json).
    input_sidecars: tuple[str,...]=()
    # Diagnostic reports that stay under their own names when the step fails (e.g. a
    # failed release gate), so the reason can be inspected; no success state is written.
    keep_outputs_on_failure: bool=False


def _spec(module,parser,common,inputs,outputs,**extra):
    return StepSpec(module,parser,frozenset(common),frozenset(inputs),dict(outputs),**extra)


STEPS: dict[str,StepSpec]={
 "validate":_spec("validate_gencode_translation",("validate_gencode_translation","build_parser"),
    {"gtf_db","genome","annotation_release"},{"gtf_db","genome","gencode_protein_fasta"},
    {"out_tsv":"gencode_translation_concordance.tsv","out_summary_json":"gencode_translation_concordance.json"},
    keep_outputs_on_failure=True),
 "fusion":_spec("fusiontoprotein",("fusiontoprotein","build_parser"),
    COMMON_KEYS,{"fusioninspector","gtf_db","genome","sample_metadata","reference_proteome"},
    {"filtered_protein_fasta":"fusion.primary.fasta","filtered_cds_fasta":"fusion.primary.cds.fasta",
     "biological_interpretation_tsv":"fusion.biological.tsv","dia_database_metadata_tsv":"fusion.metadata.tsv",
     "out_sequence_sample_tsv":None,"digested_peptide_tsv":None},
    extra_outputs=_fusion_outputs),
 "rmats":_spec("rmatstoprotein",("proteogenomic.splice_cli","build_rmats_parser"),
    COMMON_KEYS-{"sample_metadata"},
    {"gtf_db","genome","se_files","a3ss_files","a5ss_files","mxe_files","ri_files","reference_proteome","event_metadata"},
    {"out_prot_fa":"rmats.primary.fasta","out_consequence_tsv":"rmats.consequences.tsv","out_event_summary_tsv":"rmats.events.tsv",
     "out_alt_start_prot_fa":None,"out_exploratory_orf_fa":None,"out_junc_fa":None},
    derive=_derive_rescue_outputs,extra_outputs=_splice_outputs),
 "suppa":_spec("suppatoprotein",("proteogenomic.splice_cli","build_suppa_parser"),
    COMMON_KEYS,{"gtf_db","genome","event_files","psi_files","sample_metadata","reference_proteome"},
    {"out_prot_fa":"suppa.primary.fasta","out_consequence_tsv":"suppa.consequences.tsv","out_psi_summary_tsv":"suppa.psi.tsv",
     "out_alt_start_prot_fa":None,"out_exploratory_orf_fa":None,"out_junc_fa":None},
    derive=_derive_rescue_outputs,extra_outputs=_suppa_outputs),
 "merge":_spec("merge_proteogenomic_database",("merge_proteogenomic_database","build_parser"),
    {"annotation_release","organism"},{"gencode_concordance_summary","inputs","reference_fasta","contaminants_fasta"},
    {"out_fasta":"proteogenomic_database.fasta","out_metadata":"proteogenomic_metadata.tsv","out_mapping":"proteogenomic_mapping.tsv",
     "out_peptide_evidence":"proteogenomic_peptides.tsv","out_biological_interpretation":"proteogenomic_biological.tsv",
     "out_summary_tsv":"proteogenomic_summary.tsv","out_summary_json":"proteogenomic_summary.json"},
    input_sidecars=(".run_config.json",)),
 "benchmark":_spec("benchmark_variant_reconstruction",("benchmark_variant_reconstruction","build_parser"),
    set(),{"actual","truth"},
    {"out_tsv":"variant_reconstruction_benchmark.tsv","out_json":"variant_reconstruction_benchmark.json"}),
 "qc":_spec("proteogenomic_fasta_qc",("proteogenomic.qc_cli","build_parser"),
    set(),{"fasta","metadata","reference_proteome"},{"outdir":"qc"},
    extra_outputs=_qc_outputs,directory_outputs=frozenset({"outdir"}),keep_outputs_on_failure=True),
 "report":_spec("release_report",("release_report","build_parser"),
    set(),{"inputs"},{"out_tsv":"release_report.tsv","out_json":"release_report.json"}),
}

# STEPS is in pipeline order (stage 1 -> 6); steps always run in this order,
# whatever order --stage/--step options are given in.
PIPELINE_ORDER=tuple(STEPS)

# Read-only views kept for callers and tests that used the former parallel tables.
STEP_MODULES={step:spec.module for step,spec in STEPS.items()}
PARSERS={step:spec.parser for step,spec in STEPS.items()}
OUTPUT_KEYS={step:set(spec.outputs) for step,spec in STEPS.items()}


@lru_cache(maxsize=None)
def _parser(step):
    """Build each step's CLI parser once; it is only read afterwards."""
    module,factory=STEPS[step].parser
    return getattr(importlib.import_module(module),factory)()


@lru_cache(maxsize=None)
def _parser_defaults_cached(step):
    return tuple((a.dest,a.default) for a in _parser(step)._actions
                 if a.dest not in {"help",argparse.SUPPRESS} and a.default is not argparse.SUPPRESS)

def _parser_keys(step):
    return {a.dest for a in _parser(step)._actions if a.dest not in {"help",argparse.SUPPRESS}}

def _unknown(section,key,choices):
    suggestion=difflib.get_close_matches(key,sorted(choices),n=1)
    prefix="Unknown top-level workflow section" if section=="root" else "Unknown workflow option"
    return ValueError(f"{prefix} [{section}].{key}"+(f"; did you mean '{suggestion[0]}'?" if suggestion else ""))

def validate_workflow(document):
    sections={"workflow","common",*STEPS}
    for section,value in document.items():
        if section not in sections: raise _unknown("root",section,sections)
        if not isinstance(value,Mapping): raise TypeError(f"Workflow section [{section}] must be a TOML table")
    for key in document.get("workflow",{}):
        if key not in WORKFLOW_KEYS: raise _unknown("workflow",key,WORKFLOW_KEYS)
    if document.get("workflow",{}).get("profile","publication") not in {"publication","standard"}:
        raise ValueError("Only the publication policy is supported; set individual options instead of workflow.profile")
    common=set().union(*(spec.common for spec in STEPS.values()))
    for key in document.get("common",{}):
        if key not in common: raise _unknown("common",key,common)
    for step in STEPS:
        allowed=_parser_keys(step)|{"enabled"}
        for key in document.get(step,{}):
            if key not in allowed: raise _unknown(step,key,allowed)
    # Check value types against each enabled step's CLI now, not hours later when the step starts.
    for step in STEPS:
        if not _enabled(document,step): continue
        actions={a.dest:a for a in _parser(step)._actions}
        for key,value in _configured(document,step).items():
            _check_option_value(step,key,value,actions[key])

def _check_option_value(step,key,value,action):
    where=f"[{step}].{key}"
    if value is None: return
    if action.nargs==0:  # boolean switch (store_true / --x/--no-x)
        if not isinstance(value,bool): raise TypeError(f"{where} must be true or false, not {value!r}")
        if value is False and not isinstance(action,argparse.BooleanOptionalAction):
            raise TypeError(f"{where} cannot be false (the option has no --no- form); omit it instead")
        return
    if isinstance(value,bool): raise TypeError(f"{where} takes a value, not {str(value).lower()}")
    if isinstance(value,list):
        if action.nargs not in ("+","*") and not isinstance(action.nargs,int):
            raise TypeError(f"{where} takes a single value, not a list")
        if action.nargs=="+" and not value: raise ValueError(f"{where} must list at least one value")
        items=value
    else:
        items=[value]
    for item in items:
        if isinstance(item,(bool,list,dict)) or not isinstance(item,(str,int,float)):
            raise TypeError(f"{where} has an unsupported value {item!r}")
        if action.type is not None:
            try: converted=action.type(str(item)) if action.type in (int,float) else item
            except (TypeError,ValueError): raise TypeError(f"{where} expects {action.type.__name__} values, not {item!r}") from None
        else: converted=item
        if action.choices is not None and converted not in action.choices:
            raise ValueError(f"{where} must be one of {sorted(action.choices)}, not {item!r}")

def load_workflow(path):
    with Path(path).open("rb") as handle: document=tomllib.load(handle)
    validate_workflow(document); return document

def _hash_json(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _hash_file(path):
    # Memoised per path/size/mtime: genome and gtf_db are shared by several steps.
    return sha256_file(path)

def _paths(values,keys):
    """Resolve input values (files, directories and glob patterns) as producers do."""
    result=[]
    for key in sorted(keys): result.extend(resolve_input_files(values.get(key)))
    return list(dict.fromkeys(result))

def _source_files(step):
    """Python sources that determine a step's behaviour: its CLI module, the shared package, and this runner."""
    modules=[STEPS[step].module,STEPS[step].parser[0],__name__ if __name__!="__main__" else "proteogenomic_workflow"]
    files=set()
    for name in modules:
        spec=importlib.util.find_spec(name)
        if spec and spec.origin and spec.origin.endswith(".py"): files.add(Path(spec.origin).resolve())
    package=importlib.util.find_spec("proteogenomic")
    for location in (package.submodule_search_locations or []) if package else []:
        files.update(p.resolve() for p in Path(location).rglob("*.py"))
    return sorted(files)

def _source_digest(step):
    """Content digest of the code a step runs, so code fixes invalidate resume state."""
    digest=hashlib.sha256()
    for path in _source_files(step):
        digest.update(path.name.encode()+b"\0"); digest.update(path.read_bytes().replace(b"\r\n",b"\n")); digest.update(b"\0")
    return digest.hexdigest()

def _parser_defaults(step):
    return dict(_parser_defaults_cached(step))

def _configured(document,step):
    """Values set explicitly in [common] (when the step accepts them) and in the step's own section."""
    spec=STEPS[step]
    values={k:v for k,v in document.get("common",{}).items() if k in spec.common}; values.update(document.get(step,{})); values.pop("enabled",None)
    return values

def resolved_step(document,step):
    spec=STEPS[step]; values=_configured(document,step)
    out=document.get("workflow",{}).get("output_dir")
    if out:
        for key,name in spec.outputs.items():
            if name is not None: values.setdefault(key,str(Path(out)/name))
    if spec.derive: spec.derive(values)
    return values

def _tokens(name,value):
    if value is None:return []
    if value is False:return ["--no-"+name]
    if value is True:return ["--"+name]
    if isinstance(value,list):return ["--"+name,*map(str,value)]
    if isinstance(value,(str,int,float)):return ["--"+name,str(value)]
    raise TypeError(f"Unsupported value for option {name}: {type(value).__name__}")

def build_step_arguments(document,step):
    return [t for k,v in resolved_step(document,step).items() for t in _tokens(k,v)]
def _enabled(document,step):
    """A step runs when its section is present (even if empty) and enabled is not false."""
    return step in document and document[step].get("enabled",True) is not False
def selected_steps(document,requested):
    """Return configured, enabled steps in pipeline order; --step requests are filtered like --stage."""
    if not requested:return [s for s in STEPS if _enabled(document,s)]
    for step in dict.fromkeys(requested):
        if not _enabled(document,step):
            print(f"WARNING: --step {step} skipped: [{step}] is missing or has enabled = false",file=sys.stderr,flush=True)
    return [s for s in PIPELINE_ORDER if s in requested and _enabled(document,s)]

def explain(document,steps):
    for step in steps:
        configured=_configured(document,step)
        print(f"[{step}]")
        resolved=resolved_step(document,step)
        effective={**{k:v for k,v in _parser_defaults(step).items() if v is not None},**resolved}
        for key,value in sorted(effective.items()):
            if key in configured: source="configuration"
            elif key not in resolved: source="parser default"
            elif document.get("workflow",{}).get("output_dir") and STEPS[step].outputs.get(key): source="output-directory convention"
            else: source="derived default"
            print(f"  {key} = {value!r}  # {source}")

def _manifest(step,values,config_hash):
    # JSON round-trip so the in-memory manifest compares equal to the saved state file.
    return json.loads(json.dumps(_raw_manifest(step,values,config_hash),sort_keys=True,default=str))

def _input_fingerprint(step,values):
    """SHA-256 of every input file plus declared sidecars (None records an absent sidecar)."""
    fingerprint={}
    for path in _paths(values,STEPS[step].inputs):
        fingerprint[str(path)]=_hash_file(path)
        for suffix in STEPS[step].input_sidecars:
            sidecar=Path(f"{path}{suffix}")
            fingerprint.setdefault(str(sidecar),_hash_file(sidecar) if sidecar.is_file() else None)
    return fingerprint

def _raw_manifest(step,values,config_hash):
    return {"schema_version":"pgdb-workflow-run-v3","software_version":SOFTWARE_VERSION,"source_sha256":_source_digest(step),
            "step":step,"configuration_sha256":config_hash,"resolved_configuration":values,
            "parser_defaults":_parser_defaults(step),
            "input_sha256":_input_fingerprint(step,values)}

def _parser_default(step,key):
    return _parser(step).get_default(key)

def expected_outputs(step,values):
    """Files a completed step must have written; resume checks these files, never just a directory."""
    spec=STEPS[step]
    get=lambda key: values.get(key,_parser_default(step,key))
    # Parser defaults count too: an output written under a CLI default must exist for resume.
    paths=[Path(str(get(k))) for k in sorted(spec.outputs) if get(k) and k not in spec.directory_outputs]
    return spec.extra_outputs(paths,values,get) if spec.extra_outputs else paths

def _outputs_exist(step,values):
    paths=expected_outputs(step,values); return bool(paths) and all(p.is_file() for p in paths)

def _output_fingerprint(step,values):
    # Outputs are always re-read, never taken from the in-process checksum cache.
    return {str(p):sha256_file(p,use_cache=False) for p in expected_outputs(step,values)}

def _state_matches(state,manifest,step,values):
    """Resume only when configuration, inputs and code match AND every output is
    byte-identical to what the recorded successful run produced."""
    saved=dict(state); outputs=saved.pop("output_sha256",None)
    return saved==manifest and bool(outputs) and outputs==_output_fingerprint(step,values)

def _write_state(state,payload):
    """Write the success record atomically (temp file + rename)."""
    state.parent.mkdir(parents=True,exist_ok=True)
    temporary=state.with_name(state.name+".tmp")
    temporary.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8",newline="\n")
    os.replace(temporary,state)

def _quarantine_outputs(step,values):
    """Rename outputs left by a failed run to *.incomplete so nothing consumes them."""
    moved=[]
    for path in expected_outputs(step,values):
        if path.is_file():
            target=path.with_name(path.name+".incomplete"); os.replace(path,target); moved.append(str(target))
    return moved

CODE_DIR=Path(__file__).resolve().parent

def _child_environment():
    """Environment for step processes: this code tree first on PYTHONPATH, so
    ``python -m <step>`` works from any working directory, installed or not."""
    env=dict(os.environ)
    env["PYTHONPATH"]=os.pathsep.join(filter(None,[str(CODE_DIR),env.get("PYTHONPATH")]))
    env.setdefault("PYTHONIOENCODING","utf-8")
    return env

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
                text=True, encoding="utf-8", errors="replace", bufsize=1, env=_child_environment(),
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
    parser.add_argument("--step",action="append",choices=tuple(STEPS),default=[],help=argparse.SUPPRESS)
    parser.add_argument("--dry-run",action="store_true"); parser.add_argument("--explain",action="store_true"); parser.add_argument("--resume",action="store_true")
    return parser

def main(argv:Sequence[str]|None=None):
    raw=list(argv if argv is not None else sys.argv[1:]); explain_command=bool(raw and raw[0]=="explain")
    if explain_command:raw.pop(0)
    args=build_parser().parse_args(raw); document=load_workflow(args.config); settings=document.get("workflow",{})
    if args.stage:
        requested=set(implementations_for(args.stage))
        steps=[step for step in PIPELINE_ORDER if step in requested and _enabled(document,step)]
    else:
        steps=selected_steps(document,args.step)
    if not steps:raise ValueError("No enabled workflow steps were configured")
    if explain_command or args.explain:explain(document,steps);return 0
    output_dir=settings.get("output_dir")
    if args.dry_run: return _run_steps(args,document,settings,steps,output_dir)
    if output_dir: Path(output_dir).mkdir(parents=True,exist_ok=True)
    with _WorkflowLock(Path(output_dir or ".")/".proteogenomic_state"/"workflow.lock"):
        return _run_steps(args,document,settings,steps,output_dir)

class _WorkflowLock:
    """Exclusive lock on an output directory, so two runs cannot interleave outputs and state."""
    def __init__(self,path): self.path=path; self.acquired=False
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        for _attempt in range(2):
            try:
                handle=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            except FileExistsError:
                if self._remove_if_stale(): continue
                raise RuntimeError(
                    f"Another workflow run is using this output directory (lock {self.path}: "
                    f"{self.path.read_text(encoding='utf-8',errors='replace').strip()}). "
                    "If no run is active, delete the lock file and retry."
                ) from None
            with os.fdopen(handle,"w",encoding="utf-8") as lock:
                lock.write(f"pid={os.getpid()} host={socket.gethostname()} started={datetime.now(timezone.utc).isoformat()}\n")
            self.acquired=True
            return self
        raise RuntimeError(f"Could not acquire workflow lock {self.path}")
    def _remove_if_stale(self):
        """Only a lock from a dead process on this POSIX host is treated as stale."""
        try: fields=dict(item.split("=",1) for item in self.path.read_text(encoding="utf-8").split() if "=" in item)
        except OSError: return False
        if os.name!="posix" or fields.get("host")!=socket.gethostname(): return False
        try: os.kill(int(fields.get("pid","0")),0)
        except ProcessLookupError: self.path.unlink(missing_ok=True); return True
        except (PermissionError,ValueError): return False
        return False
    def __exit__(self,*_exc):
        if self.acquired: self.path.unlink(missing_ok=True)

def _run_steps(args,document,settings,steps,output_dir):
    for step in steps:
        stage=next((STAGES_BY_SLUG[slug] for slug in args.stage if step in STAGES_BY_SLUG[slug].implementations),stage_for_implementation(step))
        print(f"STAGE {stage.number}: {stage.name}", flush=True)
        values=resolved_step(document,step); state=Path(output_dir or ".")/".proteogenomic_state"/f"{step}.json"
        command=[sys.executable,"-u","-m",STEPS[step].module,*build_step_arguments(document,step)]
        log_path=Path(output_dir or ".")/"logs"/f"stage_{stage.number:02d}_{step}.log"
        resume_candidate=(args.resume or settings.get("resume")) and state.is_file() and _outputs_exist(step,values)
        # Input checksums (possibly multi-GB references) are computed only when a
        # resume decision or a state file needs them, never for a plain dry run.
        manifest=_manifest(step,values,_hash_json({"step":step,"values":values})) if resume_candidate or not args.dry_run else None
        if resume_candidate and _state_matches(json.loads(state.read_text(encoding="utf-8")),manifest,step,values):
            if not args.dry_run:
                run_logged_command(command,log_path,stage=stage,step=step,values=values,skip=True)
            print(f"SKIP {step}: configuration, input and output checksums match");continue
        print(shlex.join(command),flush=True)
        if args.dry_run:continue
        print(f"Log: {log_path}",flush=True)
        # The previous success record no longer describes the files once the step
        # starts overwriting them: remove it before running.
        state.unlink(missing_ok=True)
        try:
            returncode=run_logged_command(command,log_path,stage=stage,step=step,values=values)
        except BaseException:
            forget_file_hashes(expected_outputs(step,values))
            _report_quarantine(step,values); raise
        # Later steps may read these outputs: never reuse checksums from before the run.
        forget_file_hashes(expected_outputs(step,values))
        if returncode:
            _report_quarantine(step,values); return returncode
        if not _outputs_exist(step,values):
            missing=[str(p) for p in expected_outputs(step,values) if not p.is_file()]
            print(f"ERROR {step}: exited successfully but did not write {', '.join(missing)}",file=sys.stderr,flush=True)
            _report_quarantine(step,values); return 1
        _write_state(state,{**manifest,"output_sha256":_output_fingerprint(step,values)})
    return 0

def _report_quarantine(step,values):
    if STEPS[step].keep_outputs_on_failure:
        print(f"WARNING {step}: failed; its reports are kept for inspection but the step is not marked complete",
              file=sys.stderr,flush=True)
        return
    for path in _quarantine_outputs(step,values):
        print(f"WARNING {step}: incomplete output moved to {path}",file=sys.stderr,flush=True)
if __name__=="__main__":raise SystemExit(main())
