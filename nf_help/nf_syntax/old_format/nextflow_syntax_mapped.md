# Nextflow Syntax (Mapped, Combined Sources)

A grouped reference of Nextflow terms extracted from multiple docs pages.

**Mode:** full

## Category Index

- [Workflow](#workflow) (13 terms)
- [Process](#process) (74 terms)
- [Channel](#channel) (16 terms)
- [Operator](#operator) (48 terms)
- [CLI](#cli) (23 terms)
- [Config](#config) (29 terms)
- [Types](#types) (16 terms)
- [Script Language](#script-language) (47 terms)
- [Modules](#modules) (2 terms)
- [Files](#files) (6 terms)

## A-Z Term Index

- [accelerator](#process-accelerator) (1 related terms)
- [afterScript](#process-afterscript) (1 related terms)
- [And &](#workflow-and-) (1 related terms)
- [apptainer](#config-apptainer) (1 related terms)
- [arch](#process-arch) (1 related terms)
- [array](#process-array) (1 related terms)
- [assert](#script-language-assert) (1 related terms)
- [Assignment](#script-language-assignment) (1 related terms)
- [auth](#cli-auth) (1 related terms)
- [aws](#config-aws) (1 related terms)
- [azure](#config-azure) (1 related terms)
- [Bag<E>](#types-bage) (1 related terms)
- [beforeScript](#process-beforescript) (1 related terms)
- [Binary expressions](#script-language-binary-expressions) (1 related terms)
- [Boolean](#types-boolean) (1 related terms)
- [branch](#operator-branch) (1 related terms)
- [buffer](#operator-buffer) (1 related terms)
- [cache](#process-cache) (1 related terms)
- [Calling processes and workflows](#workflow-calling-processes-and-workflows) (1 related terms)
- [Capturing groups](#script-language-capturing-groups) (1 related terms)
- [Channel](#types-channel) (1 related terms)
- [Channels](#channel-channels) (1 related terms)
- [charliecloud](#config-charliecloud) (1 related terms)
- [clean](#cli-clean) (1 related terms)
- [clone](#cli-clone) (1 related terms)
- [Closure](#script-language-closure) (1 related terms)
- [Closures](#script-language-closures) (1 related terms)
- [clusterOptions](#process-clusteroptions) (1 related terms)
- [collate](#operator-collate) (1 related terms)
- [collect](#operator-collect) (1 related terms)
- [collectFile](#operator-collectfile) (1 related terms)
- [combine](#operator-combine) (1 related terms)
- [Commands](#cli-commands) (1 related terms)
- [Comments](#script-language-comments) (1 related terms)
- [concat](#operator-concat) (1 related terms)
- [conda](#process-conda) (1 related terms)
- [Conditional execution](#script-language-conditional-execution) (1 related terms)
- [Conditional scripts](#process-conditional-scripts) (1 related terms)
- [Config](#cli-config) (2 related terms)
- [console](#cli-console) (1 related terms)
- [Constructor call](#script-language-constructor-call) (1 related terms)
- [container](#process-container) (1 related terms)
- [containerOptions](#process-containeroptions) (1 related terms)
- [Copying files](#files-copying-files) (1 related terms)
- [count](#operator-count) (1 related terms)
- [countFasta](#operator-countfasta) (1 related terms)
- [countFastq](#operator-countfastq) (1 related terms)
- [countJson](#operator-countjson) (1 related terms)
- [countLines](#operator-countlines) (1 related terms)
- [cpus](#process-cpus) (1 related terms)
- [cross](#operator-cross) (1 related terms)
- [dag](#config-dag) (1 related terms)
- [debug](#process-debug) (1 related terms)
- [Deprecations](#script-language-deprecations) (1 related terms)
- [Directives](#process-directives) (1 related terms)
- [disk](#process-disk) (1 related terms)
- [distinct](#operator-distinct) (1 related terms)
- [docker](#config-docker) (1 related terms)
- [drop](#cli-drop) (1 related terms)
- [dump](#operator-dump) (1 related terms)
- [Duration](#types-duration) (1 related terms)
- [Dynamic directives](#process-dynamic-directives) (1 related terms)
- [Dynamic retry with backoff](#process-dynamic-retry-with-backoff) (1 related terms)
- [Dynamic string](#script-language-dynamic-string) (1 related terms)
- [Dynamic task resources](#process-dynamic-task-resources) (1 related terms)
- [Dynamic task resources with previous execution trace](#process-dynamic-task-resources-with-previous-execution-trace) (1 related terms)
- [echo](#process-echo) (1 related terms)
- [empty](#channel-empty) (1 related terms)
- [Enum](#script-language-enum) (1 related terms)
- [env](#config-env) (1 related terms)
- [Environment Variables](#process-environment-variables) (1 related terms)
- [errorStrategy](#process-errorstrategy) (1 related terms)
- [executor](#process-executor) (1 related terms)
- [Executor-specific defaults](#config-executor-specific-defaults) (1 related terms)
- [Expression statement](#script-language-expression-statement) (1 related terms)
- [Expressions](#script-language-expressions) (1 related terms)
- [ext](#process-ext) (1 related terms)
- [Factories](#channel-factories) (1 related terms)
- [fair](#process-fair) (1 related terms)
- [Feature flag](#script-language-feature-flag) (1 related terms)
- [Files](#process-files) (8 related terms)
- [Filesystem operations](#files-filesystem-operations) (1 related terms)
- [filter](#operator-filter) (1 related terms)
- [first](#operator-first) (1 related terms)
- [flatMap](#operator-flatmap) (1 related terms)
- [flatten](#operator-flatten) (1 related terms)
- [Float](#types-float) (1 related terms)
- [from](#channel-from) (1 related terms)
- [fromFilePairs](#channel-fromfilepairs) (1 related terms)
- [fromLineage](#channel-fromlineage) (1 related terms)
- [fromList](#channel-fromlist) (1 related terms)
- [fromPath](#channel-frompath) (1 related terms)
- [fromSRA](#channel-fromsra) (1 related terms)
- [fs](#cli-fs) (1 related terms)
- [Function](#script-language-function) (2 related terms)
- [fusion](#config-fusion) (1 related terms)
- [Generic options](#process-generic-options) (1 related terms)
- [google](#config-google) (1 related terms)
- [groupTuple](#operator-grouptuple) (1 related terms)
- [Hello world](#script-language-hello-world) (1 related terms)
- [help](#cli-help) (1 related terms)
- [if/else](#script-language-ifelse) (1 related terms)
- [ifEmpty](#operator-ifempty) (1 related terms)
- [Include](#script-language-include) (1 related terms)
- [Index expression](#script-language-index-expression) (1 related terms)
- [Index files](#workflow-index-files) (1 related terms)
- [info](#cli-info) (1 related terms)
- [Input files ( path )](#process-input-files-path-) (1 related terms)
- [Input repeaters ( each )](#process-input-repeaters-each-) (1 related terms)
- [Input tuples ( tuple )](#process-input-tuples-tuple-) (1 related terms)
- [Input variables ( val )](#process-input-variables-val-) (1 related terms)
- [Inputs](#process-inputs) (1 related terms)
- [Inputs and outputs (legacy)](#process-inputs-and-outputs-legacy) (1 related terms)
- [Inputs and outputs (typed)](#process-inputs-and-outputs-typed) (1 related terms)
- [inspect](#cli-inspect) (1 related terms)
- [Integer](#types-integer) (1 related terms)
- [interval](#channel-interval) (1 related terms)
- [Iterable<E>](#types-iterablee) (1 related terms)
- [Java settings](#config-java-settings) (1 related terms)
- [join](#operator-join) (1 related terms)
- [k8s](#config-k8s) (1 related terms)
- [kuberun](#cli-kuberun) (1 related terms)
- [label](#process-label) (1 related terms)
- [last](#operator-last) (1 related terms)
- [launch](#cli-launch) (1 related terms)
- [Legacy parameters](#workflow-legacy-parameters) (1 related terms)
- [lineage](#cli-lineage) (1 related terms)
- [lint](#cli-lint) (1 related terms)
- [List](#script-language-list) (1 related terms)
- [list](#cli-list) (1 related terms)
- [List<E>](#types-liste) (1 related terms)
- [Listing directories](#files-listing-directories) (1 related terms)
- [Lists](#script-language-lists) (1 related terms)
- [log](#cli-log) (1 related terms)
- [machineType](#process-machinetype) (1 related terms)
- [mail](#config-mail) (1 related terms)
- [manifest](#config-manifest) (1 related terms)
- [Map](#script-language-map) (1 related terms)
- [map](#operator-map) (1 related terms)
- [Map<K,V>](#types-mapkv) (1 related terms)
- [Maps](#script-language-maps) (1 related terms)
- [max](#operator-max) (1 related terms)
- [maxErrors](#process-maxerrors) (1 related terms)
- [maxForks](#process-maxforks) (1 related terms)
- [maxRetries](#process-maxretries) (1 related terms)
- [maxSubmitAwait](#process-maxsubmitawait) (1 related terms)
- [memory](#process-memory) (1 related terms)
- [MemoryUnit](#types-memoryunit) (1 related terms)
- [merge](#operator-merge) (1 related terms)
- [min](#operator-min) (1 related terms)
- [mix](#operator-mix) (1 related terms)
- [Modules](#process-modules) (7 related terms)
- [Multi-line strings](#script-language-multi-line-strings) (1 related terms)
- [multiMap](#operator-multimap) (1 related terms)
- [Multiple inclusions](#modules-multiple-inclusions) (1 related terms)
- [Multiple input files](#process-multiple-input-files) (1 related terms)
- [Multiple inputs](#process-multiple-inputs) (1 related terms)
- [Named workflows](#workflow-named-workflows) (1 related terms)
- [Naming outputs](#process-naming-outputs) (1 related terms)
- [Native execution](#process-native-execution) (1 related terms)
- [nextflow](#config-nextflow) (1 related terms)
- [Nextflow settings](#config-nextflow-settings) (1 related terms)
- [notification](#config-notification) (1 related terms)
- [Null](#script-language-null) (1 related terms)
- [Number](#script-language-number) (1 related terms)
- [of](#channel-of) (1 related terms)
- [Opening files](#files-opening-files) (1 related terms)
- [Operations](#types-operations) (1 related terms)
- [Operators](#channel-operators) (1 related terms)
- [Optional outputs](#process-optional-outputs) (1 related terms)
- [Options](#cli-options) (1 related terms)
- [Other settings](#config-other-settings) (1 related terms)
- [Output](#workflow-output) (10 related terms)
- [Outputs](#process-outputs) (1 related terms)
- [Parameters](#workflow-parameters) (1 related terms)
- [Params](#workflow-params) (2 related terms)
- [Parentheses](#script-language-parentheses) (1 related terms)
- [penv](#process-penv) (1 related terms)
- [Pipe |](#workflow-pipe-) (1 related terms)
- [plugin](#cli-plugin) (1 related terms)
- [pod](#process-pod) (1 related terms)
- [podman](#config-podman) (1 related terms)
- [Precedence](#script-language-precedence) (1 related terms)
- [Process](#script-language-process) (2 related terms)
- [Property expression](#script-language-property-expression) (1 related terms)
- [publishDir](#process-publishdir) (1 related terms)
- [Publishing files](#workflow-publishing-files) (1 related terms)
- [pull](#cli-pull) (1 related terms)
- [queue](#process-queue) (1 related terms)
- [randomSample](#operator-randomsample) (1 related terms)
- [Reading and writing](#files-reading-and-writing) (1 related terms)
- [reduce](#operator-reduce) (1 related terms)
- [Regular expressions](#script-language-regular-expressions) (1 related terms)
- [Remote files](#files-remote-files) (1 related terms)
- [report](#config-report) (1 related terms)
- [resourceLabels](#process-resourcelabels) (1 related terms)
- [resourceLimits](#process-resourcelimits) (1 related terms)
- [return](#script-language-return) (1 related terms)
- [run](#cli-run) (1 related terms)
- [sarus](#config-sarus) (1 related terms)
- [scratch](#process-scratch) (1 related terms)
- [Script](#process-script) (1 related terms)
- [Script declarations](#script-language-script-declarations) (1 related terms)
- [Script definitions](#script-language-script-definitions) (1 related terms)
- [Scripts A la carte](#process-scripts-a-la-carte) (1 related terms)
- [secret](#process-secret) (1 related terms)
- [secrets](#cli-secrets) (1 related terms)
- [self-update](#cli-self-update) (1 related terms)
- [Seqera Platform settings](#config-seqera-platform-settings) (1 related terms)
- [set](#operator-set) (1 related terms)
- [Set<E>](#types-sete) (1 related terms)
- [Sharing modules](#modules-sharing-modules) (1 related terms)
- [Shebang](#script-language-shebang) (1 related terms)
- [shell](#process-shell) (1 related terms)
- [Shell](#process-shell) (1 related terms)
- [shifter](#config-shifter) (1 related terms)
- [Singleton outputs](#process-singleton-outputs) (1 related terms)
- [singularity](#config-singularity) (1 related terms)
- [spack](#process-spack) (1 related terms)
- [Special operators](#workflow-special-operators) (1 related terms)
- [splitCsv](#operator-splitcsv) (1 related terms)
- [splitFasta](#operator-splitfasta) (1 related terms)
- [splitFastq](#operator-splitfastq) (1 related terms)
- [splitJson](#operator-splitjson) (1 related terms)
- [splitText](#operator-splittext) (1 related terms)
- [Stage directives](#process-stage-directives) (1 related terms)
- [stageInMode](#process-stageinmode) (1 related terms)
- [stageOutMode](#process-stageoutmode) (1 related terms)
- [Standard input ( stdin )](#process-standard-input-stdin-) (1 related terms)
- [Statements](#script-language-statements) (1 related terms)
- [storeDir](#process-storedir) (1 related terms)
- [String](#types-string) (1 related terms)
- [String interpolation](#script-language-string-interpolation) (1 related terms)
- [String replacement](#script-language-string-replacement) (1 related terms)
- [Strings](#script-language-strings) (1 related terms)
- [Stub](#process-stub) (1 related terms)
- [subscribe](#operator-subscribe) (1 related terms)
- [sum](#operator-sum) (1 related terms)
- [tag](#process-tag) (1 related terms)
- [take](#operator-take) (1 related terms)
- [Takes and emits](#workflow-takes-and-emits) (1 related terms)
- [tap](#operator-tap) (1 related terms)
- [Task properties](#process-task-properties) (1 related terms)
- [Template](#process-template) (1 related terms)
- [Ternary expression](#script-language-ternary-expression) (1 related terms)
- [throw](#script-language-throw) (1 related terms)
- [time](#process-time) (1 related terms)
- [timeline](#config-timeline) (1 related terms)
- [toInteger](#operator-tointeger) (1 related terms)
- [toList](#operator-tolist) (1 related terms)
- [topic](#channel-topic) (1 related terms)
- [toSortedList](#operator-tosortedlist) (1 related terms)
- [tower](#config-tower) (1 related terms)
- [trace](#config-trace) (1 related terms)
- [transpose](#operator-transpose) (1 related terms)
- [try/catch](#script-language-trycatch) (1 related terms)
- [Tuple](#types-tuple) (1 related terms)
- [Tuples](#script-language-tuples) (1 related terms)
- [Unary expressions](#script-language-unary-expressions) (1 related terms)
- [unique](#operator-unique) (1 related terms)
- [Unscoped options](#config-unscoped-options) (1 related terms)
- [until](#operator-until) (1 related terms)
- [Using task directive values](#process-using-task-directive-values) (1 related terms)
- [value](#channel-value) (1 related terms)
- [Value<V>](#types-valuev) (1 related terms)
- [Values](#channel-values) (1 related terms)
- [Variable](#script-language-variable) (2 related terms)
- [Variables](#script-language-variables) (1 related terms)
- [VersionNumber](#types-versionnumber) (1 related terms)
- [view](#operator-view) (1 related terms)
- [watchPath](#channel-watchpath) (1 related terms)
- [wave](#config-wave) (1 related terms)
- [When](#process-when) (1 related terms)
- [Workflow](#workflow-workflow) (5 related terms)

## Sources

- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/reference/config.html
- https://www.nextflow.io/docs/stable/workflow.html
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html
- https://www.nextflow.io/docs/stable/reference/cli.html
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/module.html
- https://www.nextflow.io/docs/stable/working-with-files.html
- https://www.nextflow.io/docs/stable/process.html
- https://www.nextflow.io/docs/stable/reference/operator.html
- https://www.nextflow.io/docs/stable/script.html
- https://www.nextflow.io/docs/stable/channel.html
- https://www.nextflow.io/docs/stable/reference/channel.html
- https://www.nextflow.io/docs/stable/reference/env-vars.html

## Workflow

### <a id="workflow-workflow"></a>Workflow

**At a glance:** A workflow can be a named workflow or an entry workflow .

**Summary:** 21 explanations, 2 constraints, 10 allowed elements, 0 examples.

#### Related Terms
- Workflow
- workflow
- Entry workflow
- Process and workflow recursion
- Workflow outputs

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/reference/config.html
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- A workflow can be a named workflow or an entry workflow .
- A named workflow consists of a name and a body, and may consist of a take , main , and emit section:
- An entry workflow has no name and may consist of a main , publish , onComplete , and onError section:
- Entry workflow definitions are ignored when a script is included as a module.
- This way, the same script can be included as a module or executed as a pipeline.
- The workflow scope provides workflow execution options.
- The following settings are available:
- A script can define up to one entry workflow , which does not have a name and serves as the entrypoint of the script:
- Processes can be invoked recursively using the recurse method.
- In the above example, the count_down process is first invoked with the value params.start .
- On each subsequent iteration, the process is invoked again using the output from the previous iteration.
- The recursion continues until the specified condition is satisfied, as defined by the until method, which terminates the recursion.
- The recursive output can also be limited using the times method:
- Workflows can also be invoked recursively:
- Limitations
- A script can define an output block which declares the top-level outputs of the workflow.
- Any channel in the workflow can be assigned to an output, including process and subworkflow outputs.
- This approach is intended to replace the publishDir directive.
- Here is a basic example:
- In the above example, the output of process fetch is assigned to the samples workflow output.
- How this output is published to a directory structure is described in the next section.

#### Constraints
- In order for a script to be executable, it must either define an entry workflow or be a code snippet as described above .
- Each output should be assigned in the publish section of the entry workflow.

#### Allowed Elements
- The take, emit, and publish sections are optional. The main: section label can be omitted if they are not specified.
- The take section consists of one or more parameters.
- The main section consists of one or more statements .
- The emit section consists of one or more emit statements . An emit statement can be a variable name , an assignment , or an expression statement . If an emit statement is an expression statement, it must be the only emit.
- Only one entry workflow may be defined in a script.
- The main: section label can be omitted if the other sections are not specified.
- The publish section consists of one or more publish statements . A publish statement is an assignment , where the assignment target is the name of a workflow output.
- The onComplete and onError sections consist of one or more statements .
- A recursive process or workflow must have matching inputs and outputs, such that the outputs for each iteration can be supplied as the inputs for the next iteration.
- Recursive workflows cannot use reduction operators such as collect , reduce , and toList , because these operators cause the recursion to hang indefinitely after the initial iteration.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-params"></a>Params

**At a glance:** The params block consists of one or more parameter declarations .

**Summary:** 10 explanations, 4 constraints, 5 allowed elements, 0 examples.

#### Related Terms
- Params block
- Parameter (legacy)

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The params block consists of one or more parameter declarations .
- A parameter declaration consists of a name, type, and an optional default value:
- A legacy parameter declaration is an assignment.
- Parameters supplied via command line options, params files, and config files take precedence over parameter definitions in a script.
- A script can declare parameters using the params block:
- The following types can be used for parameters:
- Parameters can be used in the entry workflow:
- The default value can be overridden by the command line, params file, or config file.
- Parameters from multiple sources are resolved in the order described in Pipeline parameters .
- Parameters specified on the command line are converted to the appropriate type based on the corresponding type annotation.

#### Constraints
- Only one params block may be defined in a script.
- The target should be a pipeline parameter and the source should be an expression:
- A parameter that doesn't specify a default value is a required param.
- If a required param is not given a value at runtime, the run will fail.

#### Allowed Elements
- Boolean
- Float
- Integer
- Path
- String

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-output"></a>Output

**At a glance:** The output block consists of one or more output declarations .

**Summary:** 39 explanations, 2 constraints, 9 allowed elements, 0 examples.

#### Related Terms
- Output block
- Output variables ( val )
- Output files ( path )
- Multiple output files
- Dynamic output file names
- Output environment variables ( env )
- Standard output ( stdout )
- Eval output ( eval )
- Output tuples ( tuple )
- Output directives

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/process.html
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The output block consists of one or more output declarations .
- Each output declaration consists of a name and one or more output directives for defining the output:
- See Workflow outputs for the set of available output directives.
- The val qualifier allows you to output any Nextflow variable defined in the process.
- A common use case is to output a variable that was defined in the input section, as shown in the following example:
- The output value can be a value literal, an input variable, any other Nextflow variable in the process scope, or a value expression.
- For example:
- The path qualifier allows you to output one or more files produced by the process.
- In the above example, the random_number process creates a file named result.txt which contains a random number.
- Since a path output with the same name is declared, that file is emitted by the corresponding process output.
- A downstream process or operator with a compatible input will be able to receive it.
- Refer to the process reference for the list of available options for path outputs.
- When an output file name contains a * or ?
- wildcard character, it is interpreted as a glob path matcher.
- This allows you to capture multiple files into a list and emit the list as a single value.
- It prints:
- By default, all the files matching the specified glob pattern are emitted as a single list.
- However, as the above example demonstrates, the flatten operator can be used to transform the list of files into a channel that emits each file individually.
- Some caveats on glob pattern behavior:
- Read more about glob syntax at the following link What is a glob?
- The arity option can be used to enforce the expected number of files, either as a number or a range.
- When a task completes, Nextflow will check whether the produced files for each path output match the declared arity, and fail if they do not.
- When the arity is '1' , the corresponding output will be a single file; otherwise, it will be a list of files.
- When an output file name needs to be expressed dynamically, it is possible to define it using a dynamic string which references variables in the input section or in the script global context.
- In the above example, each process execution produces an alignment file whose name depends on the actual value of the species input.
- The env qualifier allows you to output a variable defined in the process execution environment:
- The stdout qualifier allows you to output the stdout of the executed process:
- The eval qualifier allows you to capture the standard output of an arbitrary command evaluated the task shell interpreter context:
- You can use a semi-colon ; to specify multiple Bash commands on a single line, and many interpreters can execute arbitrary code on the command line, e.g.
- python -c 'print("Hello world!")' .
- If the command fails, the task will also fail.
- In Bash, you can append || true to a command to suppress any command failure.
- The tuple qualifier outputs multiple values in a single output as a tuple .
- In the above example, a blast task is executed for each pair of species and query that are received.
- Each task produces a new tuple containing the value for species and the file result .
- A tuple definition may contain any of the following qualifiers, as previously described: val , path , env and stdout .
- Files specified with the path qualifier are treated exactly the same as standalone path inputs.
- The following directives are available for each output in the output block:
- Additionally, the following options from the workflow config scope can be specified as directives:

#### Constraints
- Only one output block may be defined in a script.
- Only one-line Bash commands are supported.

#### Allowed Elements
- Input files are not included (unless includeInputs is true )
- Directories are included, unless the ** pattern is used to recurse through directories
- contentType
- enabled
- ignoreErrors
- mode
- overwrite
- storageClass
- tags

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-and-"></a>And &

**At a glance:** Reference for And &.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- And &

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The & and operator can be used to call multiple processes in parallel with the same channel(s):
- In the above snippet, the initial channel is piped to the map operator, which reverses the string value.
- Then, the result is passed to the processes greet and to_upper , which are executed in parallel.
- Each process outputs a channel, and the two channels are combined using the mix operator.
- Finally, the result is printed using the view operator.
- The same code can also be written as:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-calling-processes-and-workflows"></a>Calling processes and workflows

**At a glance:** Reference for Calling processes and workflows.

**Summary:** 7 explanations, 0 constraints, 2 allowed elements, 0 examples.

#### Related Terms
- Calling processes and workflows

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- Processes and workflows are called like functions, passing their inputs as arguments:
- Processes and workflows have a few extra rules for how they can be called:
- The areturn valuea of a process or workflow call is the process outputs or workflow emits, respectively.
- The return value can be assigned to a variable or passed into another call:
- Named outputs can be accessed as properties of the return value:
- As a convenience, process and workflow outputs can also be accessed without first assigning to a variable, by using the .out property of the process or workflow name:
- Workflows can be composed in the same way:

#### Allowed Elements
- Processes and workflows can only be called by workflows
- A given process or workflow can only be called once in a given workflow. To use a process or workflow multiple times in the same workflow, use Module aliases .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-index-files"></a>Index files

**At a glance:** Each output can create an index file of the values that were published.

**Summary:** 8 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Index files

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- Each output can create an index file of the values that were published.
- An index file preserves the structure of channel values, including metadata, which is simpler than encoding this information with directories and file names.
- The index file can be a CSV ( .csv ), JSON ( .json ), or YAML ( .yml , .yaml ) file.
- For example:
- The above example will write the following CSV file to results/samples.csv :
- You can customize the index file with additional directives, for example:
- This example will produce the following index file:
- See Output directives for the list of available index directives.

#### Constraints
- The channel values should be files, lists, or maps.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-legacy-parameters"></a>Legacy parameters

**At a glance:** Reference for Legacy parameters.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Legacy parameters

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- Parameters can be declared by assigning a params property to a default value:
- The default value can be overridden by the command line, params file, or config file.
- Parameters from multiple sources are resolved in the order described in Pipeline parameters .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-named-workflows"></a>Named workflows

**At a glance:** Reference for Named workflows.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Named workflows

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- A named workflow is a workflow that can be called by other workflows:
- The above example defines a workflow named my_workflow which is called by the entry workflow.
- Both hello and bye could be any other process or workflow.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-parameters"></a>Parameters

**At a glance:** Parameters can be declared in a Nextflow script with the params block or with legacy parameter declarations.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Parameters

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- Parameters can be declared in a Nextflow script with the params block or with legacy parameter declarations.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-pipe-"></a>Pipe |

**At a glance:** Reference for Pipe |.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Pipe |

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The | pipe operator can be used to chain processes, operators, and workflows:
- The above snippet defines a process named greet and invokes it with the input channel.
- The result is then piped to the map operator, which converts each string to uppercase, and finally to the view operator which prints it.
- The same code can also be written as:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-publishing-files"></a>Publishing files

**At a glance:** Reference for Publishing files.

**Summary:** 15 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Publishing files

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The top-level output directory of a workflow run can be set using the -output-dir command-line option or the outputDir config option:
- The default output directory is results in the launch directory.
- By default, all output files are published to the output directory.
- Each output in the output block can define where files are published using the path directive.
- For example:
- The following directory structure will be created:
- All files received by an output will be published into the specified directory.
- Lists and maps are recursively scanned for nested files.
- The path directive can also be a closure which defines a custom publish path for each channel value:
- The above example will publish each channel value to a different subdirectory.
- In this case, each pair of FASTQ files will be published to a subdirectory based on the sample ID.
- The closure can even define a different path for each individual file using the >> operator:
- Each >> specifies a source file and publish target .
- If the publish target ends with a slash, it is treated as the directory in which source files are published.
- Otherwise, it is treated as the target filename of a source file.

#### Constraints
- The source file should be a file or collection of files, and the publish target should be a directory or file name.
- Only files that are published with the >> operator are saved to the output directory.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-special-operators"></a>Special operators

**At a glance:** The following operators have a special meaning when used in a workflow with process and workflow calls.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Special operators

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following operators have a special meaning when used in a workflow with process and workflow calls.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-takes-and-emits"></a>Takes and emits

**At a glance:** Reference for Takes and emits.

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Takes and emits

#### Source
- https://www.nextflow.io/docs/stable/workflow.html

<details>
<summary>Show full details</summary>

#### Explanation
- The take: section is used to declare the inputs of a named workflow:
- Inputs can be specified like arguments when calling the workflow:
- The emit: section is used to declare the outputs of a named workflow:
- When calling the workflow, the output can be accessed using the out property, i.e.
- my_workflow.out .
- If an output is assigned to a name, the name can be used to reference the output from the calling workflow.
- For example:
- The result of the above workflow can be accessed using my_workflow.out.my_data .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Process

### <a id="process-modules"></a>Modules

**At a glance:** Environment Modules is a package manager that allows you to dynamically configure your execution environment and easily switch between multiple versions of the same software tool.

**Summary:** 35 explanations, 2 constraints, 2 allowed elements, 0 examples.

#### Related Terms
- module
- Module inclusion
- Module directory
- Module aliases
- Module parameters
- Module templates
- Module binaries

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/module.html

<details>
<summary>Show full details</summary>

#### Explanation
- Environment Modules is a package manager that allows you to dynamically configure your execution environment and easily switch between multiple versions of the same software tool.
- If it is available in your system you can use it with Nextflow in order to configure the processes execution environment in your pipeline.
- In a process definition you can use the module directive to load a specific module version to be used in the process execution environment.
- For example:
- You can repeat the module directive for each module you need to load.
- Alternatively multiple modules can be specified in a single module directive by separating all the module names by using a : (colon) character as shown below:
- You can include any definition from a module into a Nextflow script using the include keyword.
- The above snippet imports a process named cat , defined in the module, into the main execution context.
- This way, cat can be invoked in the workflow scope.
- Nextflow implicitly looks for the script file ./some/module.nf , resolving the path against the including script location.
- Module includes are subject to the following rules:
- A module can be defined as a directory with the same name as the module and with a script named main.nf .
- Module directories allow the use of module scoped binaries scripts.
- See [Module binaries] for details.
- When including definition from a module, it's possible to specify an alias with the as keyword.
- Aliasing allows you to avoid module name clashes, by assigning them different names in the including context.
- You can also include the same definition multiple times under different names:
- A module can define parameters using the same syntax as a Nextflow workflow script:
- When including a module, the module will first use parameters from the including context.
- The above snippet prints:
- The addParams option can be used to pass parameters to the module without adding them to the including scope.
- Alternatively, the params option can be used to pass parameters to module without adding them to the including scope, and without inheriting any parameters from the including scope.
- Process script templates can be included alongside a module in the templates directory.
- For example, suppose we have a project L with a module that defines two processes, P1 and P2, both of which use templates.
- The template files can be made available in the local templates directory:
- Then, we have a second project A with a workflow that includes P1 and P2:
- Finally, we have a third project B with a workflow that also includes P1 and P2:
- With the possibility to keep the template files inside the project L, A and B can use the modules defined in L without any changes.
- A future project C would do the same, just cloning L (if not available on the system) and including its module.
- Beside promoting the sharing of modules across pipelines, there are several advantages to keeping the module template under the script path:
- Having multiple template locations enables a structured project organization.
- If a project has several modules, and they all use templates, the project could group module scripts and their templates as needed.
- Modules can define binary scripts that are locally scoped to the processes defined by the tasks.
- To enable this feature, set the following flag in your pipeline script or configuration file:
- Those scripts will be made accessible like any other command in the task environment, provided they have been granted the Linux execute permissions.

#### Constraints
- When defined as a directory, the module must be included by specifying the module directory path:
- The binary scripts must be placed in the module directory names <module-dir>/resources/usr/bin :

#### Allowed Elements
- Relative paths must begin with the ./ prefix.
- Include statements are not allowed from within a workflow. They must occur at the script level.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-files"></a>Files

**At a glance:** Reference for Getting file attributes.

**Summary:** 27 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Getting file attributes
- Reading and writing an entire file
- Appending to a file
- Reading a file line by line
- Advanced file reading
- Advanced file writing
- Remote file staging
- Dynamic input file names

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The file() method returns a Path , which has several methods for retrieving metadata about the file:
- See the Path reference for the list of available methods.
- Given a file variable, created with the file() method as shown previously, reading a file is as easy as getting the fileas text property, which returns the file content as a string:
- Similarly, you can save a string to a file by assigning it to the fileas text property:
- Binary data can be managed in the same way, just using the file property bytes instead of text .
- Thus, the following example reads the file and returns its content as a byte array:
- Or you can save a byte array to a file:
- In order to append a string value to a file without erasing existing content, you can use the append() method:
- Or use the left shift operator, a more idiomatic way to append text content to a file:
- In order to read a text file line by line you can use the method readLines() provided by the file object, which returns the file content as a list of strings:
- This can also be written in a more idiomatic syntax:
- The classes Reader and InputStream provide fine-grained control for reading text and binary files, respectively.
- The method newReader() creates a Reader object for the given file that allows you to read the content as single characters, lines or arrays of characters:
- The method withReader() works similarly, but automatically calls the close() method for you when you have finished processing the file.
- So, the previous example can be written more simply as:
- The methods newInputStream() and withInputStream() work similarly.
- The main difference is that they create an InputStream object useful for writing binary data.
- The Writer and OutputStream classes provide fine-grained control for writing text and binary files, respectively, including low-level operations for single characters or bytes, and support for big files.
- For example, given two file objects sourceFile and targetFile , the following code copies the first fileas content into the second file, replacing all U characters with X :
- When a process input file resides on a different file system than the work directory, Nextflow copies the file into the work directory using an appropriate Java SDK.
- Remote files are staged in a subdirectory of the work directory with the form stage-<session-id>/<hash>/<filename> , where <hash> is determined by the remote file path.
- If multiple tasks request the same remote file, the file will be downloaded once and reused by each task.
- These files can be reused by resumed runs with the same session ID.
- When the input file name is specified by using the name option or a string literal, you can also use other input values as variables in the file name string.
- For example:
- In the above example, the input file name is determined by the current value of the x input value.
- This approach allows input files to be staged in the task directory with a name that is coherent with the current execution context.

#### Constraints
- To process a big file, use the method eachLine() , which reads only a single line at a time into memory:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-environment-variables"></a>Environment Variables

**At a glance:** The env qualifier allows you to define an environment variable in the process execution context based on the input value.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Input environment variables ( env )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The env qualifier allows you to define an environment variable in the process execution context based on the input value.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-accelerator"></a>accelerator

**At a glance:** The accelerator directive allows you to request hardware accelerators (e.g.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- accelerator

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The accelerator directive allows you to request hardware accelerators (e.g.
- GPUs) for the task execution.
- For example:
- The above examples will request 4 GPUs of type nvidia-tesla-k80 .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-afterscript"></a>afterScript

**At a glance:** The afterScript directive allows you to execute a custom (Bash) snippet immediately after the main process has run.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- afterScript

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The afterScript directive allows you to execute a custom (Bash) snippet immediately after the main process has run.
- This may be useful to clean up your staging area.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-arch"></a>arch

**At a glance:** The arch directive allows you to define the CPU architecture to build the software in use by the processa task.

**Summary:** 7 explanations, 0 constraints, 6 allowed elements, 0 examples.

#### Related Terms
- arch

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The arch directive allows you to define the CPU architecture to build the software in use by the processa task.
- For example:
- The example above declares that the CPU generic architecture is linux/x86_64 (X86 64 bit), and more specifically that the microarchitecture is cascadelake (a specific generation of Intel CPUs).
- This directive is currently used by the following Nextflow functionalities:
- Allowed values for the arch directive are as follows, grouped by equivalent family (choices available for the sake of compatibility):
- Examples of values for the architecture target option are cascadelake , icelake , zen2 and zen3 .
- See the Spack documentation for the full and up-to-date list of meaningful targets.

#### Allowed Elements
- by the spack directive, to build microarchitecture-optimised applications;
- by the Wave containers service, to build containers for one of the generic families of CPU architectures (see below);
- by the spack strategy within Wave containers , to optimise the container builds for specific CPU microarchitectures.
- X86 64 bit: linux/x86_64 , x86_64 , linux/amd64 , amd64
- ARM 64 bit: linux/aarch64 , aarch64 , linux/arm64 , arm64 , linux/arm64/v8
- ARM 64 bit, older generation: linux/arm64/v7

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-array"></a>array

**At a glance:** The array directive allows you to submit tasks as job arrays for executors that support it.

**Summary:** 10 explanations, 4 constraints, 20 allowed elements, 0 examples.

#### Related Terms
- array

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The array directive allows you to submit tasks as job arrays for executors that support it.
- A job array is a collection of jobs with the same resource requirements and the same script (parameterized by an index).
- Job arrays incur significantly less scheduling overhead compared to individual jobs, and as a result they are preferred by HPC schedulers where possible.
- For example:
- Nextflow currently supports job arrays for the following executors:
- A process using job arrays will collect tasks and submit each batch as a job array when it is ready.
- Any aleftovera tasks will be submitted as a partial job array.
- Once a job array is submitted, each achilda task is executed as an independent job.
- Any tasks that fail (and can be retried) will be retried without interfering with the tasks that succeeded.
- Retried tasks are submitted individually rather than through a job array, in order to allow for the use of dynamic resources .

#### Constraints
- The directive should be specified with a given array size, along with an executor that supports job arrays.
- The following directives must be uniform across all tasks in a process that uses job arrays, because these directives are specified once for the entire job array:
- For cloud-based executors like AWS Batch, or when using Fusion with any executor, the following additional directives must be uniform:
- When using Wave, the following additional directives must be uniform:

#### Allowed Elements
- AWS Batch
- Google Cloud Batch
- LSF
- PBS/Torque
- PBS Pro
- SGE
- SLURM
- accelerator
- clusterOptions
- cpus
- disk
- machineType
- memory
- queue
- resourceLabels
- resourceLimits
- time
- container
- containerOptions
- conda

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-beforescript"></a>beforeScript

**At a glance:** The beforeScript directive allows you to execute a custom (Bash) snippet before the main process script is run.

**Summary:** 5 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- beforeScript

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The beforeScript directive allows you to execute a custom (Bash) snippet before the main process script is run.
- This may be useful to initialise the underlying cluster environment or for other custom initialisation.
- For example:
- cloud batch executors, Kubernetes).
- Otherwise, the beforeScript will be executed outside the container.

#### Constraints
- When the process is containerized (using the container directive), the beforeScript will be executed in the container only if the executor is container-native (e.g.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-cache"></a>cache

**At a glance:** The cache directive allows you to store the process results to a local cache.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- cache

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The cache directive allows you to store the process results to a local cache.
- When the cache is enabled and the pipeline is launched with the resume option, any task executions that are already cached will be re-used.
- See the Caching and resuming page for more information about how the cache works.
- The cache is enabled by default, but you can disable it for a specific process by setting the cache directive to false .
- For example:
- The following options are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-clusteroptions"></a>clusterOptions

**At a glance:** The clusterOptions directive allows the usage of any native configuration option accepted by your cluster submit command.

**Summary:** 5 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- clusterOptions

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The clusterOptions directive allows the usage of any native configuration option accepted by your cluster submit command.
- You can use it to request non-standard resources or use settings that are specific to your cluster and not supported out of the box by Nextflow.
- The cluster options can be a string:
- The cluster options can also be a string list:
- Grid executors that require one option per line will write each option to a separate line, while grid executors that allow multiple options per line will write all options to a single line, the same as with a string.

#### Constraints
- This form is useful to control how the options are split across lines when it is required by the scheduler.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-conda"></a>conda

**At a glance:** The conda directive allows for the definition of the process dependencies using the Conda package manager.

**Summary:** 11 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- conda

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The conda directive allows for the definition of the process dependencies using the Conda package manager.
- Nextflow automatically sets up an environment for the given package names listed by in the conda directive.
- For example:
- Multiple packages can be specified separating them with a blank space e.g.
- bwa=0.7.15 fastqc=0.11.5 .
- The name of the channel from where a specific package needs to be downloaded can be specified using the usual Conda notation i.e.
- prefixing the package with the channel name as shown here bioconda::bwa=0.7.15 .
- The conda directive also allows the specification of a Conda environment file path or the path of an existing environment directory.
- See the Conda environments page for further details.
- The conda scope controls the creation of Conda environments by the Conda package manager.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-conditional-scripts"></a>Conditional scripts

**At a glance:** The script section is like a function that returns a string.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Conditional scripts

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The script section is like a function that returns a string.
- This means that you can write arbitrary code to determine the script, as long as the final statement is a string.
- If-else statements based on task inputs can be used to produce a different script.
- For example:
- In the above example, the process will execute one of several scripts depending on the value of the mode parameter.
- By default it will execute the tcoffee command.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-container"></a>container

**At a glance:** The container directive allows you to execute the process script in a Docker container.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- container

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The container directive allows you to execute the process script in a Docker container.
- It requires the Docker daemon to be running in machine where the pipeline is executed, i.e.
- the local machine when using the local executor or the cluster nodes when the pipeline is deployed through a grid executor.
- For example:
- Simply replace in the above script dockerbox:tag with the name of the Docker image you want to use.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-containeroptions"></a>containerOptions

**At a glance:** The containerOptions directive allows you to specify any container execution option supported by the underlying container engine (ie.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- containerOptions

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The containerOptions directive allows you to specify any container execution option supported by the underlying container engine (ie.
- Docker, Singularity, etc).
- mount a custom path:

#### Constraints
- This can be useful to provide container settings only for a specific process e.g.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-cpus"></a>cpus

**At a glance:** Reference for cpus.

**Summary:** 2 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- cpus

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- For example:
- See also: penv , memory , time , queue , maxForks

#### Constraints
- The cpus directive allows you to define the number of (logical) CPU required by the processa task.
- This directive is required for tasks that execute multi-process or multi-threaded commands/tools and it is meant to reserve enough CPUs when a pipeline task is executed through a cluster resource manager.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-debug"></a>debug

**At a glance:** By default the stdout produced by the commands executed in all processes is ignored.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- debug

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- By default the stdout produced by the commands executed in all processes is ignored.
- By setting the debug directive to true , you can forward the process stdout to the current top running process stdout file, showing it in the shell terminal.
- For example:
- Without specifying debug true , you won't see the Hello string printed out when executing the above example.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-directives"></a>Directives

**At a glance:** Directives are optional settings that affect the execution of the current process.

**Summary:** 9 explanations, 1 constraints, 8 allowed elements, 0 examples.

#### Related Terms
- Directives

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- Directives are optional settings that affect the execution of the current process.
- By default, directives are evaluated when the process is defined.
- However, if the value is a dynamic string or closure, it will be evaluated separately for each task, which allows task-specific variables like task and val inputs to be used.
- Refer to the Executors page for more information about each executor.
- Refer to the process reference for the full list of process directives.
- If you are new to Nextflow, here are some commonly-used operators to learn first:
- General:
- Resource requirements:
- Software dependencies:

#### Constraints
- Some directives are only supported by specific executors.

#### Allowed Elements
- errorStrategy : strategy for handling task failures
- executor : the executor with which to execute tasks
- tag : a semantic name used to differentiate between task executions of the same process
- cpus : the number of CPUs to request for each task
- memory : the amount of memory to request for each task
- time : the amount of walltime to request for each task
- conda : list of conda packages to provision for tasks
- container : container image to use for tasks

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-disk"></a>disk

**At a glance:** The disk directive allows you to define how much local disk storage the process is allowed to use.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- disk

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The disk directive allows you to define how much local disk storage the process is allowed to use.
- For example:
- The following memory unit suffix can be used when specifying the disk value:
- See MemoryUnit for more information.
- See also: cpus , memory time , queue and Dynamic task resources .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-dynamic-directives"></a>Dynamic directives

**At a glance:** A directive can be assigned dynamically , during the process execution, so that its actual value can be evaluated based on the process inputs.

**Summary:** 8 explanations, 1 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Dynamic directives

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- A directive can be assigned dynamically , during the process execution, so that its actual value can be evaluated based on the process inputs.
- To be defined dynamically, the directiveas value needs to be expressed using a closure .
- For example:
- In the above example, the queue directive is evaluated dynamically, depending on the input value entries .
- When it is larger than 100, jobs will be submitted to the long queue, otherwise the short queue will be used.
- All directives can be assigned a dynamic value except the following:
- Dynamic directives can be specified without a closure when using the strict syntax :
- Directives will be evaluated dynamically if they reference task inputs.

#### Constraints
- Process configuration options must still be specified with a closure to be dynamic.

#### Allowed Elements
- executor
- label
- maxForks

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-dynamic-retry-with-backoff"></a>Dynamic retry with backoff

**At a glance:** network congestion.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Dynamic retry with backoff

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- network congestion.
- In these cases immediately re-executing the task will likely result in the identical error.
- A retry with an exponential backoff delay can better recover these error conditions:

#### Constraints
- There are cases in which the required execution resources may be temporary unavailable e.g.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-dynamic-task-resources"></a>Dynamic task resources

**At a glance:** Itas a very common scenario that different instances of the same process may have very different needs in terms of computing resources.

**Summary:** 12 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Dynamic task resources

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- Itas a very common scenario that different instances of the same process may have very different needs in terms of computing resources.
- In such situations requesting, for example, an amount of memory too low will cause some tasks to fail.
- Instead, using a higher limit that fits all the tasks in your execution could significantly decrease the execution priority of your jobs.
- Dynamic directives can be used to adjust the requested task resources when a task fails and is re-executed.
- For example:
- In the above example the memory and execution time limits are defined dynamically.
- The first time the process is executed the task.attempt is set to 1 , thus it will request 2 GB of memory and 1 hour of walltime.
- If the task execution fails with an exit status between 137 and 140, the task is re-executed; otherwise, the run is terminated immediately.
- The re-executed task will have task.attempt set to 2 , and will request 4 GB of memory and 2 hours of walltime.
- The maxRetries directive sets the maximum number of times the same task can be re-executed.
- Task resources can also be defined in terms of task inputs.
- In this example, each task requests 8 GB of memory, plus the size of the input file rounded up to the next GB.

#### Constraints
- This way, each task requests only as much memory as it needs based on the size of the inputs.
- The specific function that you use should be tuned for each process.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-dynamic-task-resources-with-previous-execution-trace"></a>Dynamic task resources with previous execution trace

**At a glance:** Task resource requests can be updated relative to the trace record metrics of the previous task attempt.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Dynamic task resources with previous execution trace

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- Task resource requests can be updated relative to the trace record metrics of the previous task attempt.
- The metrics can be accessed through the task.previousTrace variable.
- For example:
- In the above example, the memory is set according to previous trace record metrics.
- In the first attempt, when no trace metrics are available, it is set to 1 GB.
- In each subsequent attempt, the requested memory is doubled.
- See Trace file for more information about trace records.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-echo"></a>echo

**At a glance:** Reference for echo.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- echo

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-errorstrategy"></a>errorStrategy

**At a glance:** The errorStrategy directive allows you to define how the process manages an error condition.

**Summary:** 11 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- errorStrategy

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The errorStrategy directive allows you to define how the process manages an error condition.
- By default, when an error status is returned by the executed script (i.e.
- when it ends with a non-zero exit status), the process stops immediately, forcing the entire pipeline to terminate.
- The following error strategies are available:
- When setting the errorStrategy directive to ignore the process doesn't stop on an error condition, it just reports a message notifying you of the error event.
- For example:
- In this case, the workflow will complete successfully and return an exit status of 0.
- However, if you set workflow.failOnIgnore = true in your Nextflow configuration, the workflow will return a non-zero exit status and report the failed tasks as an error.
- The retry error strategy allows you to re-submit for execution a process returning an error condition.
- The number of times a failing process is re-executed is defined by the maxRetries and maxErrors directives.
- See also: maxErrors , maxRetries and Dynamic task resources .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-executor"></a>executor

**At a glance:** The executor defines the underlying system where processes are executed.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- executor

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The executor defines the underlying system where processes are executed.
- By default a process uses the executor defined globally in the nextflow.config file.
- The executor directive allows you to configure what executor has to be used by the process, overriding the default configuration.
- The following executors are available:
- The following example shows how to set the process's executor:
- The executor scope controls various executor behaviors.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-ext"></a>ext

**At a glance:** The ext is a special directive used as namespace for user custom process directives.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- ext

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The ext is a special directive used as namespace for user custom process directives.
- This can be useful for advanced configuration options.
- For example:
- In the above example, the process container version is controlled by ext.version , and the script supports additional command line arguments through ext.args .
- The ext directive can be set in the process definition:
- Or in the Nextflow configuration:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-fair"></a>fair

**At a glance:** The fair directive, when enabled, guarantees that process outputs will be emitted in the order in which they were received.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fair

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The fair directive, when enabled, guarantees that process outputs will be emitted in the order in which they were received.
- For example:
- The above example produces:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-generic-options"></a>Generic options

**At a glance:** Reference for Generic options.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Generic options

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following options are available for all process outputs:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-input-files-path-"></a>Input files ( path )

**At a glance:** The path qualifier allows you to provide input files to the process execution context.

**Summary:** 15 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Input files ( path )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The path qualifier allows you to provide input files to the process execution context.
- Nextflow will stage the files into the process execution directory, and they can be accessed in the script by using the specified input name.
- For example:
- In the above example, all the files ending with the suffix .fa are sent over the channel proteins .
- These files are received by the process, which executes a BLAST query on each of them.
- Itas worth noting that in the above example, the name of the file in the file-system is not used.
- You can access the file without even knowing its name, because you can reference it in the process script by the input name.
- There may be cases where your task needs to use a file whose name is fixed, i.e.
- it does not have to change along with the actual provided file.
- In this case, you can specify a fixed name with the name attribute in the input file parameter definition, as shown in the following example:
- or, using a shorter syntax:
- The previous example can be re-written as shown below:
- In this example, each file received by the process is staged with the name query.fa in a different execution context (i.e.
- the folder where a task is executed).
- Channel factories like channel.fromPath produce file objects, but a path input can also accept a string literal path.

#### Constraints
- The string value should be an absolute path, i.e.
- it must be prefixed with a / character or a supported URI protocol ( file:// , http:// , s3:// , etc), and it cannot contain special characters ( \n , etc).

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-input-repeaters-each-"></a>Input repeaters ( each )

**At a glance:** The each qualifier allows you to repeat the execution of a process for each item in a collection, each time a new value is received.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Input repeaters ( each )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The each qualifier allows you to repeat the execution of a process for each item in a collection, each time a new value is received.
- For example:
- In the above example, each time a file of sequences is emitted from the sequences channel, the process executes three tasks, each running a T-coffee alignment with a different value for the mode parameter.
- This behavior is useful when you need to repeat the same task over a given set of parameters.
- Input repeaters can be applied to files as well.
- In the above example, each sequence input file emitted by the sequences channel triggers six alignment tasks, three with the regular method against each library file, and three with the espresso method.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-input-tuples-tuple-"></a>Input tuples ( tuple )

**At a glance:** The tuple qualifier groups multiple values into a single input definition.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Input tuples ( tuple )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The tuple qualifier groups multiple values into a single input definition.
- Each element in the tuple is associated with a corresponding element in the tuple definition.
- For example:
- In the above example, the tuple input consists of the value x and the file input.txt .
- A tuple definition may contain any of the following qualifiers, as previously described: val , env , path and stdin .
- Files specified with the path qualifier are treated exactly the same as standalone path inputs.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-input-variables-val-"></a>Input variables ( val )

**At a glance:** The val qualifier accepts any data type.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Input variables ( val )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The val qualifier accepts any data type.
- It can be accessed in the process script by using the specified input name, as shown in the following example:
- In the above example, the process is executed three times: once for each value emitted by the num channel.
- The resulting output is similar to the one shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs"></a>Inputs

**At a glance:** The input section defines the input of a process, similar to function arguments.

**Summary:** 8 explanations, 2 constraints, 6 allowed elements, 0 examples.

#### Related Terms
- Inputs

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The input section defines the input of a process, similar to function arguments.
- The input section follows the syntax shown below:
- An input declaration consists of a qualifier and a name .
- The input qualifier defines the type of data to be received.
- This information is used by Nextflow to apply the semantic rules associated with each qualifier, and handle it properly depending on the target execution platform (grid, cloud, etc).
- The examples provided in the following sections demonstrate how a process is invoked.
- The following input qualifiers are available:
- See process reference for the full list of input methods and options.

#### Constraints
- A process may have at most one input section, which must contain at least one input declaration.
- When a process is invoked in a workflow, it must be provided a channel or dataflow value for each input in the process input section, similar to calling a function with specific arguments.

#### Allowed Elements
- val : Access the input value by name in the process script.
- path : Handle the input value as a path, staging the file properly in the execution context.
- env : Use the input value to set an environment variable in the process script.
- stdin : Forward the input value to the process stdin special file.
- tuple : Handle a group of input values having any of the above qualifiers.
- each : Execute the process for each element in the input collection.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs-and-outputs-legacy"></a>Inputs and outputs (legacy)

**At a glance:** Reference for Inputs and outputs (legacy).

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Inputs and outputs (legacy)

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs-and-outputs-typed"></a>Inputs and outputs (typed)

**At a glance:** Reference for Inputs and outputs (typed).

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Inputs and outputs (typed)

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-label"></a>label

**At a glance:** The label directive allows the annotation of processes with mnemonic identifier of your choice.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- label

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The label directive allows the annotation of processes with mnemonic identifier of your choice.
- For example:
- The same label can be applied to more than a process and multiple labels can be applied to the same process using the label directive more than one time.
- Labels are useful to organize workflow processes in separate groups which can be referenced in the configuration file to select and configure a subset of processes having similar computing requirements.
- See Process selectors for more information.
- See also: resourceLabels

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-machinetype"></a>machineType

**At a glance:** The machineType can be used to specify a predefined Google Compute Platform machine type when running using the Google Batch , or when using the autopools feature of the Azure Batch executor .

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- machineType

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The machineType can be used to specify a predefined Google Compute Platform machine type when running using the Google Batch , or when using the autopools feature of the Azure Batch executor .
- This directive is optional and if specified overrides the cpus and memory directives:
- See also: cpus and memory .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxerrors"></a>maxErrors

**At a glance:** The maxErrors directive allows you to specify the maximum number of times a process can fail when using the retry error strategy.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- maxErrors

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The maxErrors directive allows you to specify the maximum number of times a process can fail when using the retry error strategy.
- By default this directive is disabled, you can set it as shown in the example below:
- See also: errorStrategy and maxRetries .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxforks"></a>maxForks

**At a glance:** The maxForks directive allows you to define the maximum number of process instances that can be executed in parallel.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- maxForks

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The maxForks directive allows you to define the maximum number of process instances that can be executed in parallel.
- By default this value is equals to the number of CPU cores available minus 1.
- If you want to execute a process in a sequential manner, set this directive to one.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxretries"></a>maxRetries

**At a glance:** The maxRetries directive allows you to define the maximum number of times a process instance can be re-submitted in case of failure.

**Summary:** 2 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- maxRetries

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The maxRetries directive allows you to define the maximum number of times a process instance can be re-submitted in case of failure.
- See also: errorStrategy and maxErrors .

#### Constraints
- This value is applied only when using the retry error strategy.
- By default only one retry is allowed, you can increase this value as shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxsubmitawait"></a>maxSubmitAwait

**At a glance:** The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue without being executed.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- maxSubmitAwait

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue without being executed.
- Elapsed this time the task execution will fail.
- When used along with retry error strategy, it can be useful to re-schedule the task to a difference queue or resource requirement.
- For example:
- In the above example the task is submitted to the spot-compute on the first attempt ( task.submitAttempt==1 ).
- If the task execution does not start in the 10 minutes, a failure is reported and a new submission is attempted using the queue named on-demand-compute .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-memory"></a>memory

**At a glance:** The memory directive allows you to define how much memory the process is allowed to use.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- memory

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The memory directive allows you to define how much memory the process is allowed to use.
- For example:
- The following memory unit suffix can be used when specifying the memory value:
- See MemoryUnit for more information.
- See also: cpus , time , queue and Dynamic task resources .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-multiple-input-files"></a>Multiple input files

**At a glance:** A path input can also accept a collection of files instead of a single value.

**Summary:** 12 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Multiple input files

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- A path input can also accept a collection of files instead of a single value.
- In this case, the input variable will be a list.
- When the input has a fixed file name and a collection of files is received by the process, the file name will be appended with a numerical suffix representing its ordinal position in the list.
- For example:
- will output:
- The target input file name may contain the * and ?
- wildcards, which can be used to control the name of staged files.
- The following table shows how the wildcards are replaced depending on the cardinality of the received input collection.
- The following example shows how a wildcard can be used in the input file definition:
- The arity option can be used to enforce the expected number of files, either as a number or a range.
- When a task is executed, Nextflow will check whether the received files for each path input match the declared arity, and fail if they do not.
- When the arity is '1' , the corresponding input variable will be a single file; otherwise, it will be a list of files.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-multiple-inputs"></a>Multiple inputs

**At a glance:** A process can declare multiple inputs, which allows it to accept inputs from multiple dataflow sources.

**Summary:** 9 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Multiple inputs

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- A process can declare multiple inputs, which allows it to accept inputs from multiple dataflow sources.
- When a process is defined with multiple inputs, it waits for a value from each input and launches a new task with the combined values.
- When one of the inputs is a channel, the process repeats until all values in the channel are consumed.
- If the channel is empty, the process will not launch any tasks.
- For example:
- The above example executes the echo process three times.
- The dataflow value x is reused for each value in y .
- It outputs:
- See also: Singleton outputs .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-naming-outputs"></a>Naming outputs

**At a glance:** The emit option is used to define the name of a process output, which can be used to access the output by name in the calling workflow.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Naming outputs

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The emit option is used to define the name of a process output, which can be used to access the output by name in the calling workflow.
- For example:
- See Calling processes and workflows for more details.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-native-execution"></a>Native execution

**At a glance:** The exec section executes the given code without launching a job.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Native execution

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The exec section executes the given code without launching a job.
- For example:
- will display:
- A native process is very similar to a function .
- However, it provides additional capabilities such as parallelism, caching, and progress logging.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-optional-outputs"></a>Optional outputs

**At a glance:** Normally, if a specified output is not produced by the task, the task will fail.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Optional outputs

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- Normally, if a specified output is not produced by the task, the task will fail.
- Setting optional: true will cause the task to not fail, and instead emit nothing to the corresponding output channel.
- In this example, the process is normally expected to produce an output.txt file, but in this case, if the file is missing, the task will not fail.

#### Constraints
- The output channel will only contain values for those tasks that produced output.txt .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-outputs"></a>Outputs

**At a glance:** Reference for Outputs.

**Summary:** 9 explanations, 1 constraints, 6 allowed elements, 0 examples.

#### Related Terms
- Outputs

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following functions are available in the output: and topic: sections of a typed process:
- The output section defines the outputs of a process, similar to a function return.
- The output section follows the syntax shown below:
- An output declaration consists of a qualifier and a name .
- Some optional attributes can also be specified.
- When a process is invoked, each process output is returned as a channel (except under certain conditions ).
- The examples provided in the following sections demonstrate how to access the outputs of a process.
- The following output qualifiers are available:
- Refer to the process reference for the full list of available output methods and options.

#### Constraints
- A process may have at most one output section, which must contain at least one output declaration.

#### Allowed Elements
- val : Emit the variable with the specified name.
- path : Emit a file produced by the process with the specified name.
- env : Emit the variable defined in the process environment with the specified name.
- stdout : Emit the stdout of the executed process.
- tuple : Emit multiple values.
- eval : Emit the result of a script or command evaluated in the task execution context.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-penv"></a>penv

**At a glance:** The penv directive allows you to define the parallel environment to be used when submitting a parallel task to the SGE resource manager.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- penv

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The penv directive allows you to define the parallel environment to be used when submitting a parallel task to the SGE resource manager.
- For example:
- This configuration depends on the parallel environment provided by your grid engine installation.
- Refer to your cluster documentation or contact your admin to learn more about this.
- See also: cpus , memory , time

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-pod"></a>pod

**At a glance:** The pod directive allows the definition of pod specific settings, such as environment variables, secrets, and config maps, when using the Kubernetes executor.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- pod

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The pod directive allows the definition of pod specific settings, such as environment variables, secrets, and config maps, when using the Kubernetes executor.
- For example:
- The above snippet defines an environment variable named MESSAGE whose value is 'hello world' .
- When defined in the Nextflow configuration file, a pod setting can be defined as a map:
- Or as a list of maps:
- The following options are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-publishdir"></a>publishDir

**At a glance:** The publishDir directive allows you to publish the process output files to a specified folder.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- publishDir

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The publishDir directive allows you to publish the process output files to a specified folder.
- For example:
- The above example splits the string Hola into file chunks of a single byte.
- When complete the chunk_* output files are published into the /data/chunks folder.
- By default files are published to the target folder creating a symbolic link for each process output that links the file produced into the process working directory.
- This behavior can be modified using the mode option, for example:
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-queue"></a>queue

**At a glance:** The queue directive allows you to set the queue where jobs are scheduled when using a grid based executor in your pipeline.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- queue

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The queue directive allows you to set the queue where jobs are scheduled when using a grid based executor in your pipeline.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-resourcelabels"></a>resourceLabels

**At a glance:** The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies to the computing resource used to carry out the process execution.

**Summary:** 4 explanations, 1 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- resourceLabels

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies to the computing resource used to carry out the process execution.
- Resource labels can be specified using the syntax shown below:
- Resource labels are currently supported by the following executors:
- See also: label

#### Constraints
- The limits and the syntax of the corresponding cloud provider should be taken into consideration when using resource labels.

#### Allowed Elements
- AWS Batch
- Azure Batch
- Google Cloud Batch
- Kubernetes

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-resourcelimits"></a>resourceLimits

**At a glance:** The resourceLimits directive allows you to specify environment-specific limits for task resource requests.

**Summary:** 8 explanations, 0 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- resourceLimits

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The resourceLimits directive allows you to specify environment-specific limits for task resource requests.
- Resource limits can be specified in a process as follows:
- Or in the Nextflow configuration:
- Resource limits can be defined for the following directives:
- Resource limits are a useful way to specify environment-specific limits alongside tasks with dynamic resources .
- Normally, if a task requests more resources than can be provisioned (e.g.
- a task requests 32 cores but the largest node in the cluster has 24), the task will either fail or cause the pipeline to hang forever as it will never be scheduled.
- If the resourceLimits directive is defined with these limits, the task resources will be automatically reduced to comply with these limits before the job is submitted.

#### Allowed Elements
- cpus
- disk
- memory
- time

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-scratch"></a>scratch

**At a glance:** The scratch directive allows you to execute the process in a temporary folder that is local to the execution node.

**Summary:** 7 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- scratch

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The scratch directive allows you to execute the process in a temporary folder that is local to the execution node.
- This is useful when your pipeline is launched by using a grid executor, because it allows you to decrease the NFS overhead by running the pipeline processes in a temporary directory in the local disk of the actual execution node.
- In its basic form simply specify true at the directive value, as shown below:
- By doing this, it tries to execute the script in the directory defined by the variable $TMPDIR in the execution node.
- If this variable does not exist, it will create a new temporary directory by using the Linux command mktemp .
- Nextflow creates a subdirectory within the scratch directory for each task and automatically deletes it once the task completes.
- The following values are supported:

#### Constraints
- Only the files declared as output in the process definition will be copied in the pipeline working area.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-script"></a>Script

**At a glance:** The script section defines, as a string expression, the script that is executed by the process.

**Summary:** 14 explanations, 4 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Script

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The script section defines, as a string expression, the script that is executed by the process.
- The script string is executed as a Bash script in the host environment.
- It can be any command or script that you would normally execute on the command line or in a Bash script.
- The script section can be a simple string or a multi-line string.
- The latter approach makes it easier to write scripts with multiple commands spanning multiple lines.
- For example:
- As explained in the script tutorial section, strings can be defined using single-quotes or double-quotes, and multi-line strings are defined by three single-quote or three double-quote characters.
- There is a subtle but important difference between them.
- Like in Bash, strings delimited by a " character support variable substitutions, while strings delimited by ' do not.
- In the above code fragment, the $db variable is replaced by the actual value defined elsewhere in the pipeline script.
- When you need to access a system environment variable in your script, you have two options.
- If you don't need to access any Nextflow variables, you can define your script section with single-quotes:
- Otherwise, you can define your script with double-quotes and escape the system environment variables by prefixing them with a back-slash \ character, as shown in the following example:
- Nextflow replaces it with the actual value before executing the script.

#### Constraints
- A process may contain only one script, and if the script guard is not explicitly declared, the script must be the final statement in the process definition.
- Naturally, the script may only use commands that are available in the host environment.
- In this example, $MAX is a Nextflow variable that must be defined elsewhere in the pipeline script.
- Meanwhile, $DB is a Bash variable that must exist in the execution environment, and Bash will replace it with the actual value during execution.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-scripts-a-la-carte"></a>Scripts A la carte

**At a glance:** The process script is interpreted by Nextflow as a Bash script by default, but you are not limited to Bash.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Scripts A la carte

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The process script is interpreted by Nextflow as a Bash script by default, but you are not limited to Bash.
- You can use your favourite scripting language (Perl, Python, R, etc), or even mix them in the same pipeline.
- A pipeline may be composed of processes that execute very different tasks.
- With Nextflow, you can choose the scripting language that best fits the task performed by a given process.
- For example, for some processes R might be more useful than Perl, whereas for others you may need to use Python because it provides better access to a library or an API, etc.
- To use a language other than Bash, simply start your process script with the corresponding shebang .
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-secret"></a>secret

**At a glance:** The secret directive allows a process to access secrets.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- secret

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The secret directive allows a process to access secrets.
- Secrets can be added to a process as follows:
- See Secrets for more information.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-shell"></a>shell

**At a glance:** The shell directive allows you to define a custom shell command for process scripts.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- shell

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The shell directive allows you to define a custom shell command for process scripts.
- By default, script blocks are executed with /bin/bash -ue .
- The same directive could be specified in your Nextflow configuration as follows:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-shell"></a>Shell

**At a glance:** The shell section is a string expression that defines the script that is executed by the process.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Shell

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The shell section is a string expression that defines the script that is executed by the process.
- It is an alternative to the Script definition with one important difference: it uses the exclamation mark !
- character, instead of the usual dollar $ character, to denote Nextflow variables.
- This way, it is possible to use both Nextflow and Bash variables in the same script without having to escape the latter, which makes process scripts easier to read and maintain.
- For example:
- In the above example, $USER is treated as a Bash variable, while !{str} is treated as a Nextflow variable.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-singleton-outputs"></a>Singleton outputs

**At a glance:** Reference for Singleton outputs.

**Summary:** 4 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Singleton outputs

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- For example:
- In the above example, the echo process is invoked with a regular value that is wrapped in a dataflow value.
- As a result, echo returns a dataflow value and greet is executed three times.
- See also: Multiple inputs .

#### Constraints
- When a process is only supplied with dataflow values, regular values, or no inputs, it returns outputs as dataflow values.
- If the call to echo was changed to echo( channel.of('hello') ) , the process would instead return a channel, and greet would be executed only once.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-spack"></a>spack

**At a glance:** The spack directive allows for the definition of the process dependencies using the Spack package manager.

**Summary:** 9 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- spack

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The spack directive allows for the definition of the process dependencies using the Spack package manager.
- Nextflow automatically sets up an environment for the given package names listed by in the spack directive.
- For example:
- Multiple packages can be specified separating them with a blank space, e.g.
- bwa@0.7.15 fastqc@0.11.5 .
- The spack directive also allows the specification of a Spack environment file path or the path of an existing environment directory.
- See the Spack environments page for further details.
- The spack scope controls the creation of a Spack environment by the Spack package manager.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stage-directives"></a>Stage directives

**At a glance:** Reference for Stage directives.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Stage directives

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following directives can be used in the stage: section of a typed process:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stageinmode"></a>stageInMode

**At a glance:** The stageInMode directive defines how input files are staged into the process work directory.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- stageInMode

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The stageInMode directive defines how input files are staged into the process work directory.
- The following values are allowed:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stageoutmode"></a>stageOutMode

**At a glance:** The stageOutMode directive defines how output files are staged out from the scratch directory to the process work directory.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- stageOutMode

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The stageOutMode directive defines how output files are staged out from the scratch directory to the process work directory.
- The following values are allowed:
- See also: scratch .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-standard-input-stdin-"></a>Standard input ( stdin )

**At a glance:** The stdin qualifier allows you to forward the input value to the standard input of the process script.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Standard input ( stdin )

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The stdin qualifier allows you to forward the input value to the standard input of the process script.
- For example:
- will output:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-storedir"></a>storeDir

**At a glance:** The storeDir directive allows you to define a directory that is used as a permanent cache for your process results.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- storeDir

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The storeDir directive allows you to define a directory that is used as a permanent cache for your process results.
- In more detail, it affects the process execution in two main ways:
- The following example shows how to use the storeDir directive to create a directory containing a BLAST database for each species specified by an input parameter:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stub"></a>Stub

**At a glance:** Reference for Stub.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Stub

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- You can define a command stub , which replaces the actual process command when the -stub-run or -stub command-line option is enabled:
- The stub section can be defined before or after the script section.
- When the pipeline is executed with the -stub-run option and a process's stub is not defined, the script section is executed.
- This feature makes it easier to quickly prototype the workflow logic without using the real commands.
- The developer can use it to provide a dummy script that mimics the execution of the real one in a quicker manner.
- In other words, it is a way to perform a dry-run.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-tag"></a>tag

**At a glance:** The tag directive allows you to associate each process execution with a custom label, so that it will be easier to identify them in the log file or in the trace execution report.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- tag

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The tag directive allows you to associate each process execution with a custom label, so that it will be easier to identify them in the log file or in the trace execution report.
- For example:
- The above snippet will print a log similar to the following one, where process names contain the tag value:
- See also Trace execution report

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-task-properties"></a>Task properties

**At a glance:** Reference for Task properties.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Task properties

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following task properties are defined in the process body:
- Additionally, the directive values for the given task can be accessed via task.<directive> .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-template"></a>Template

**At a glance:** Process scripts can be externalized to template files, which allows them to be reused across different processes and tested independently from the pipeline execution.

**Summary:** 8 explanations, 1 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Template

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- Process scripts can be externalized to template files, which allows them to be reused across different processes and tested independently from the pipeline execution.
- A template can be used in place of an embedded script using the template function in the script section:
- By default, Nextflow looks for the template script in the templates directory located alongside the Nextflow script in which the process is defined.
- An absolute path can be used to specify a different location.
- However, this practice is discouraged because it hinders pipeline portability.
- An example template script is provided below:
- Variables prefixed with the dollar character ( $ ) are interpreted as Nextflow variables when the template script is executed by Nextflow and Bash variables when executed directly.
- For example, the above script can be executed from the command line by providing each input as an environment variable:

#### Constraints
- The following caveats should be considered:

#### Allowed Elements
- Template scripts are recommended only for Bash scripts. Languages that do not prefix variables with $ (e.g. Python and R) canat be executed directly as a template script.
- Variables escaped with \$ will be interpreted as Bash variables when executed by Nextflow, but will not be interpreted as variables when executed from the command line. This practice should be avoided to ensure that the template script behaves consistently.
- Template variables are evaluated even if they are commented out in the template script. If a template variable is missing, it will cause the pipeline to fail regardless of where it occurs in the template.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-time"></a>time

**At a glance:** The time directive allows you to define how long a process is allowed to run.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- time

#### Source
- https://www.nextflow.io/docs/stable/reference/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The time directive allows you to define how long a process is allowed to run.
- For example:
- The following time unit suffixes can be used when specifying the duration value:
- See Duration for more information.
- See also: cpus , memory , queue and Dynamic task resources .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-using-task-directive-values"></a>Using task directive values

**At a glance:** The task object also contains the values of all process directives for the given task, which allows you to access these settings at runtime.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Using task directive values

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The task object also contains the values of all process directives for the given task, which allows you to access these settings at runtime.
- For examples:
- In the above snippet, task.cpus and task.memory hold the values for the cpus directive and memory directive directives, respectively, which were resolved for this task based on the process configuration.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-when"></a>When

**At a glance:** The condition can be any expression that returns a boolean value.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- When

#### Source
- https://www.nextflow.io/docs/stable/process.html

<details>
<summary>Show full details</summary>

#### Explanation
- The condition can be any expression that returns a boolean value.
- It can be useful to enable/disable the process execution depending on the state of various inputs and parameters.
- For example:

#### Constraints
- The when section allows you to define a condition that must be satisfied in order to execute the process.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Channel

### <a id="channel-channels"></a>Channels

**At a glance:** A dataflow channel (or simply channel ) is an asynchronous sequence of values.

**Summary:** 2 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Channels

#### Source
- https://www.nextflow.io/docs/stable/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- A dataflow channel (or simply channel ) is an asynchronous sequence of values.
- For example:

#### Constraints
- The values in a channel cannot be accessed directly, but only through an operator or process.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-empty"></a>empty

**At a glance:** The channel.empty factory method, by definition, creates a channel that doesn't emit any value.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- empty

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.empty factory method, by definition, creates a channel that doesn't emit any value.
- See also: ifEmpty .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-factories"></a>Factories

**At a glance:** A channel can be created by factories in the channel namespace.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Factories

#### Source
- https://www.nextflow.io/docs/stable/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- A channel can be created by factories in the channel namespace.
- For example, the channel.fromPath() factory creates a channel from a file name or glob pattern, similar to the files() function:
- See Channel factories for the full list of channel factories.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-from"></a>from

**At a glance:** Reference for from.

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- from

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.from method allows you to create a channel emitting any sequence of values that are specified as the method argument, for example:
- The first line in this example creates a variable ch which holds a channel object.
- This channel emits the values specified as a parameter in the from method.
- Thus the second line will print the following:
- The following example shows how to create a channel from a range of numbers or strings:
- Thus the following two declarations produce an identical result even though in the first case the items are specified as multiple arguments while in the second case as a single list object argument:
- But when more than one argument is provided, they are always managed as single emissions.
- Thus, the following example creates a channel emitting three entries each of which is a list containing two elements:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromfilepairs"></a>fromFilePairs

**At a glance:** The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob pattern provided by the user.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fromFilePairs

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob pattern provided by the user.
- The matching files are emitted as tuples in which the first element is the grouping key of the matching pair and the second element is the list of files (sorted in lexicographical order).
- For example:
- It will produce an output similar to the following:
- Multiple glob patterns can be specified using a list:
- Alternatively, it is possible to implement a custom file pair grouping strategy providing a closure which, given the current file as parameter, returns the grouping key.
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromlineage"></a>fromLineage

**At a glance:** Reference for fromLineage.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fromLineage

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.fromLineage factory creates a channel that emits files from the lineage store that match the given key-value params:
- The above snippet emits files published by the given workflow run that are labeled as alpha and beta .
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromlist"></a>fromList

**At a glance:** Reference for fromList.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fromList

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.fromList method allows you to create a channel emitting the values provided as a list of elements, for example:
- Prints:
- See also: channel.of factory method.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-frompath"></a>fromPath

**At a glance:** You can create a channel emitting one or more file paths by using the channel.fromPath method and specifying a path string as an argument.

**Summary:** 17 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fromPath

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- You can create a channel emitting one or more file paths by using the channel.fromPath method and specifying a path string as an argument.
- For example:
- The above line creates a channel and binds it to a Path object for the specified file.
- Whenever the channel.fromPath argument contains a * or ?
- wildcard character it is interpreted as a glob path matcher.
- This example creates a channel and emits as many Path items as there are files with txt extension in the /data/big folder.
- The first line returns a channel emitting the files ending with the suffix .fa in the data folder and recursively in all its sub-folders.
- Finally the last example emits two files: data/file_1.fq and data/file_2.fq .
- Multiple paths or glob patterns can be specified using a list:
- In order to include hidden files, you need to start your pattern with a period character or specify the hidden: true option.
- The first example returns all hidden files in the specified path.
- The second one returns all hidden files ending with the .fa suffix.
- Finally the last example returns all files (hidden and non-hidden) in that path.
- it won't return directory paths.
- You can use the type option specifying the value file , dir or any in order to define what kind of paths you want.
- The first example will return all directory paths ending with the b suffix, while the second will return any file or directory starting with a a prefix.
- Available options:

#### Constraints
- While the second one only emits the files which have the same suffix in any sub-folder in the data path.
- By default a glob pattern only looks for regular file paths that match the specified criteria, i.e.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromsra"></a>fromSRA

**At a glance:** The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ files matching the specified criteria i.e project or accession number(s).

**Summary:** 8 explanations, 1 constraints, 2 allowed elements, 0 examples.

#### Related Terms
- fromSRA

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ files matching the specified criteria i.e project or accession number(s).
- For example:
- It returns:
- Multiple accession IDs can be specified using a list object:
- This method uses the NCBI ESearch API behind the scenes, therefore it allows the use of any query term supported by this API.
- Available options:
- Available retry policy properties:
- The following code snippet shows an example for using the channel.fromSRA factory method with a custom retryPolicy .

#### Constraints
- To access the ESearch API, you must provide your NCBI API keys through one of the following ways:

#### Allowed Elements
- The apiKey option: channel . fromSRA ( ids , apiKey: '0123456789abcdef' )
- The NCBI_API_KEY variable in your environment: export NCBI_API_KEY = 0123456789abcdef

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-interval"></a>interval

**At a glance:** The interval method emits an incrementing index (starting from zero) at a periodic interval.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- interval

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The interval method emits an incrementing index (starting from zero) at a periodic interval.
- For example:
- The above snippet will emit 0, 1, 2, and so on, every second, forever.
- You can use an operator such as take or until to close the channel based on a stopping condition.
- An optional closure can be used to transform the index.
- Additionally, returning channel.STOP will close the channel.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-of"></a>of

**At a glance:** Reference for of.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- of

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.of method allows you to create a channel that emits the arguments provided to it, for example:
- The first line in this example creates a variable ch which holds a channel object.
- This channel emits the arguments supplied to the of method.
- Thus the second line prints the following:
- Ranges of values are expanded accordingly:
- Prints:
- See also: channel.fromList factory method.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-operators"></a>Operators

**At a glance:** Operators are symbols that perform specific functions on one or more values, and generally make code easier to read.

**Summary:** 15 explanations, 0 constraints, 9 allowed elements, 0 examples.

#### Related Terms
- Operators

#### Source
- https://www.nextflow.io/docs/stable/script.html
- https://www.nextflow.io/docs/stable/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- Operators are symbols that perform specific functions on one or more values, and generally make code easier to read.
- This section highlights some of the most commonly used operators.
- The == and != operators can be used to test whether any two values are equal (or not equal):
- Comparison operators can be used to compare two values:
- Logical operators can be used to perform Boolean logic:
- The in and !in operators can be used to test membership , i.e.
- whether a collection contains a value:
- Arithmetic operators can be used to do math:
- Some arithmetic operators can be used with other types of values.
- For example, + can be used to concatenate lists, maps, and strings:
- Channel operators, or operators for short, are functions that consume and produce channels.
- Because channels are asynchronous, operators are necessary to manipulate the values in a channel.
- Operators are particularly useful for implementing glue logic between processes.
- Commonly used operators include:
- See Operators for the full list of operators.

#### Allowed Elements
- combine : emit the combinations of two channels
- collect : collect the values from a channel into a list
- filter : select the values in a channel that satisfy a condition
- flatMap : transform each value from a channel into a list and emit each list element separately
- groupTuple : group the values from a channel based on a grouping key
- join : join the values from two channels based on a matching key
- map : transform each value from a channel with a mapping function
- mix : emit the values from multiple channels
- view : print each value in a channel to standard output

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-topic"></a>topic

**At a glance:** A topic channel is a channel that can receive values from many sources implicitly based on a matching topic name .

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- topic

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- A topic channel is a channel that can receive values from many sources implicitly based on a matching topic name .
- A process output can be assigned to a topic using the topic option on an output, for example:
- The channel.topic function returns the topic channel for the given name, which can be used as input to a process or operator, like any other channel:
- This approach is a convenient way to collect related items from many different sources without explicitly connecting them (e.g.
- using the mix operator).
- See also: Generic options for process outputs.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-value"></a>value

**At a glance:** The channel.value function creates a dataflow value bound to the given argument.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- value

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.value function creates a dataflow value bound to the given argument.
- For example:
- The first line creates a dataflow value bound to the string 'Hello there' .
- The second line creates a dataflow value bound to the list [1,2,3,4,5] , which is treated as a single value in dataflow logic.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-values"></a>Values

**At a glance:** A dataflow value is an asynchronous value.

**Summary:** 4 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Values

#### Source
- https://www.nextflow.io/docs/stable/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- A dataflow value is an asynchronous value.
- Dataflow values can be created using the channel.value factory, and they are created by processes (under certain conditions ).
- For example:
- See Value<V> for the set of available methods for dataflow values.

#### Constraints
- A dataflow value cannot be accessed directly, but only through an operator or process.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-watchpath"></a>watchPath

**At a glance:** The channel.watchPath method watches a folder for one or more files matching a specified pattern.

**Summary:** 10 explanations, 1 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- watchPath

#### Source
- https://www.nextflow.io/docs/stable/reference/channel.html

<details>
<summary>Show full details</summary>

#### Explanation
- The channel.watchPath method watches a folder for one or more files matching a specified pattern.
- As soon as there is a file that meets the specified condition, it is emitted over the channel that is returned by the watchPath method.
- The condition on files to watch can be specified by using * or ?
- wildcard characters i.e.
- by specifying a glob path matching criteria.
- For example:
- Optionally, it is possible to provide a second argument that specifies what event(s) to watch.
- The supported events are:
- You can specify more than one of these events by using a comma separated string as shown below:
- See also: channel.fromPath factory method.

#### Constraints
- By default it watches only for new files created in the specified folder.

#### Allowed Elements
- create : A new file is created (default)
- modify : A file is modified
- delete : A file is deleted

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Operator

### <a id="operator-branch"></a>branch

**At a glance:** Returns: multiple channels

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- branch

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: multiple channels
- The branch operator forwards each item from a source channel to one of multiple output channels, based on a selection criteria.
- The selection criteria is a closure that defines, for each output channel, a unique label followed by a boolean expression.
- When an item is received, it is routed to the first output channel whose expression evaluates to true .
- For example:
- A fallback condition can be specified using true as the last branch condition:
- The value emitted to each branch can be customized with an expression statement (or statements) after the branch condition:
- The branchCriteria() method can be used to create a branch criteria as a variable that can be passed as an argument to any number of branch operations, as shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-buffer"></a>buffer

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- buffer

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The buffer operator collects items from a source channel into subsets and emits each subset separately.
- This operator has multiple variants:
- See also: collate

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collate"></a>collate

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- collate

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The collate operator collects items from a source channel into groups of N items.
- This operator has multiple variants:
- See also: buffer

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collect"></a>collect

**At a glance:** Returns: dataflow value

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- collect

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The collect operator collects all items from a source channel into a list and emits it as a single item:
- An optional closure can be used to transform each item before it is collected:
- Available options:
- See also: toList , toSortedList

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collectfile"></a>collectFile

**At a glance:** Returns: channel

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- collectFile

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The collectFile operator collects the items from a source channel and saves them to one or more files, emitting the collected file(s).
- This operator has multiple variants:
- The following example shows how to use a closure to collect and sort all sequences in a FASTA file from shortest to longest:
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-combine"></a>combine

**At a glance:** Returns: channel

**Summary:** 6 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- combine

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The combine operator produces the combinations (i.e.
- cross product, Cartesian product) of two source channels, or a channel and a list (as the right operand), emitting each combination separately.
- For example:
- The by option can be used to combine items that share a matching key.
- See also: cross , join

#### Constraints
- The value should be the zero-based index of the tuple, or a list of indices.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-concat"></a>concat

**At a glance:** Returns: channel

**Summary:** 5 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- concat

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The concat operator emits the items from two or more source channels into a single output channel.
- Each source channel is emitted in the order in which it was specified.
- For example:
- See also: mix

#### Constraints
- In other words, given N channels, the items from the i+1 -th channel are emitted only after all of the items from the i -th channel have been emitted.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-count"></a>count

**At a glance:** Returns: dataflow value

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- count

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The count operator computes the total number of items in a source channel and emits it:
- An optional filter can be provided to select which items to count.
- The selection criteria can be a literal value, a regular expression , a type qualifier (i.e.
- Java class), or a boolean predicate.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countfasta"></a>countFasta

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- countFasta

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- Counts the total number of records in a channel of FASTA files, equivalent to splitFasta | count .
- See splitFasta for the list of available options.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countfastq"></a>countFastq

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- countFastq

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- Counts the total number of records in a channel of FASTQ files, equivalent to splitFastq | count .
- See splitFastq for the list of available options.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countjson"></a>countJson

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- countJson

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- Counts the total number of records in a channel of JSON files, equivalent to splitJson | count .
- See splitJson for the list of available options.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countlines"></a>countLines

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- countLines

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- Counts the total number of lines in a channel of text files, equivalent to splitText | count .
- See splitLines for the list of available options.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-cross"></a>cross

**At a glance:** Returns: channel

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- cross

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The cross operator emits every pairwise combination of two channels for which the pair has a matching key.
- By default, the key is defined as the first entry in a list or map, or the value itself for any other data type.
- For example:
- An optional closure can be used to define the matching key for each item:
- There are two important caveats when using the cross operator:
- See also: combine

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-distinct"></a>distinct

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- distinct

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The distinct operator forwards a source channel with consecutively repeated items removed, such that each emitted item is different from the preceding one:
- An optional closure can be used to transform each value before it is evaluated for distinct-ness:
- See also: unique

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-dump"></a>dump

**At a glance:** Returns: channel

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- dump

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The dump operator prints each item in a source channel when the pipeline is executed with the -dump-channels command-line option, otherwise it does nothing.
- It is a useful way to inspect and debug channels quickly without having to modify the pipeline script.
- The tag option can be used to select which channels to dump:
- Then, you can run your pipeline with -dump-channels plus1 or -dump-channels exp2 to dump the content of either channel.
- Multiple tag names can be specified as a comma-separated list.
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-filter"></a>filter

**At a glance:** Returns: channel

**Summary:** 5 explanations, 3 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- filter

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The filter operator emits the items from a source channel that satisfy a condition, discarding all other items.
- The filter condition can be a literal value, a regular expression , a type qualifier (i.e.
- Java class), or a boolean predicate.
- The following example filters a channel using a boolean predicate, which is a closure that returns a boolean value.

#### Constraints
- The following example filters a channel with a regular expression that only matches strings beginning with a :
- The following example filters a channel with the Number type qualifier so that only numbers are emitted:
- In this case, the predicate is used to select only odd numbers:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-first"></a>first

**At a glance:** Returns: dataflow value

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- first

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The first operator emits the first item in a source channel, or the first item that matches a condition.
- The condition can be a regular expression , a type qualifier (i.e.
- Java class), or a boolean predicate.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-flatmap"></a>flatMap

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- flatMap

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The flatMap operator applies a mapping function to each item from a source channel.
- When the mapping function returns a list, each element in the list is emitted separately:
- When the mapping function returns a map, each key-value pair in the map is emitted separately:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-flatten"></a>flatten

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- flatten

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The flatten operator flattens each item from a source channel that is a list or other collection, such that each element in each collection is emitted separately:
- As shown in the above example, deeply nested collections are also flattened.
- See also: flatMap

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-grouptuple"></a>groupTuple

**At a glance:** Returns: channel

**Summary:** 12 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- groupTuple

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The groupTuple operator collects lists (i.e.
- tuples ) from a source channel into groups based on a grouping key.
- A new tuple is emitted for each distinct key.
- To be more precise, the operator transforms a sequence of tuples like (K, V, W, ..) into a sequence of tuples like (K, list(V), list(W), ..) .
- For example:
- By default, the first element of each tuple is used as the grouping key.
- The by option can be used to specify a different index, or list of indices.
- For example, to group by the second element of each tuple:
- By default, if you don't specify a size, the groupTuple operator will not emit any groups until all inputs have been received.
- In cases where the size of each group varies based on the grouping key, you can use the built-in groupKey() function, which allows you to define a different expected size for each group:
- Available options:

#### Constraints
- If possible, you should always try to specify the number of expected elements in each group using the size option, so that each group can be emitted as soon as it's ready.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-ifempty"></a>ifEmpty

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- ifEmpty

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The ifEmpty operator emits a source channel, or a default value if the source channel is empty (doesn't emit any value):
- The default value can also be a closure , in which case the closure is evaluated and the result is emitted when the source channel is empty.
- See also: empty channel factory

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-join"></a>join

**At a glance:** Returns: channel

**Summary:** 10 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- join

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The join operator emits the inner product of two source channels using a matching key.
- To be more precise, the operator transforms a sequence of tuples like (K, V1, V2, ..) and (K, W1, W1, ..) into a sequence of tuples like (K, V1, V2, .., W1, W2, ..) .
- For example:
- By default, the first element of each item is used as the key.
- The by option can be used to specify a different index, or list of indices.
- By default, unmatched items are discarded.
- The remainder option can be used to emit them at the end:
- Available options:
- See also: combine , cross

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-last"></a>last

**At a glance:** Returns: dataflow value

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- last

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The last operator emits the last item from a source channel:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-map"></a>map

**At a glance:** Returns: channel

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- map

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The map operator applies a mapping function to each item from a source channel:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-max"></a>max

**At a glance:** Returns: dataflow value

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- max

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The max operator emits the item with the greatest value from a source channel:
- An optional closure can be used to control how the items are compared.
- The closure can be a mapping function , which transforms each item before it is compared, or a comparator function , which defines how to compare two items more generally.
- The following examples show how to find the longest string in a channel:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-merge"></a>merge

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 2 allowed elements, 0 examples.

#### Related Terms
- merge

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The merge operator joins the items from two or more channels into a new channel:
- An optional closure can be used to control how two items are merged:
- The merge operator may return a channel or value depending on the inputs:

#### Allowed Elements
- If the first argument is a channel, the merge operator returns a channel merging as many values as are available for all inputs. Dataflow values are re-used for each merged value.
- If the first argument is a dataflow value, the merge operator returns a dataflow value, merging the first value from each input, regardless of whether there are channel inputs with additional values.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-min"></a>min

**At a glance:** Returns: dataflow value

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- min

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The min operator emits the item with the lowest value from a source channel:
- An optional closure can be used to control how the items are compared.
- The closure can be a mapping function , which transforms each item before it is compared, or a comparator function , which defines how to compare two items more generally.
- The following examples show how to find the shortest string in a channel:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-mix"></a>mix

**At a glance:** Returns: channel

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- mix

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The mix operator emits the items from two or more source channels into a single output channel:
- The items in the mixed output channel may appear in any order, regardless of which source channel they came from.
- Thus, the previous example could also output the following:
- See also: concat

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-multimap"></a>multiMap

**At a glance:** Returns: multiple channels

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- multiMap

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: multiple channels
- The multiMap operator applies a set of mapping functions to a source channel, producing a separate output channel for each mapping function.
- The multi-map criteria is a closure that defines, for each output channel, a label followed by a mapping expression.
- For example:
- Multiple labels can share the same mapping expression using the following shorthand:
- The above example creates two channels as before, but now they both receive the same items.
- You can use the multiMapCriteria() method to create a multi-map criteria as a variable that can be passed as an argument to any number of multiMap operations, as shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-randomsample"></a>randomSample

**At a glance:** Returns: channel

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- randomSample

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The randomSample operator emits a randomly-selected subset of items from a source channel:
- The above snippet will print 10 randomly-selected numbers between 1 and 100 (without replacement).
- An optional second parameter can be used to set the initial seed for the random number generator, which ensures that the randomSample operator produces the same pseudo-random sequence across runs:
- The above example will print 10 randomly-selected numbers between 1 and 100 (without replacement).
- Each subsequent script execution will produce the same sequence.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-reduce"></a>reduce

**At a glance:** Returns: dataflow value

**Summary:** 6 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- reduce

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The reduce operator applies an accumulator function sequentially to each item in a source channel, and emits the final accumulated value.
- This process is repeated for each item in the source channel.
- For example:
- By default, the first item is used as the initial accumulated value.
- You can optionally specify a different initial value as shown below:

#### Constraints
- The accumulator function takes two parameters a the accumulated value and the i -th emitted item a and it should return the accumulated result, which is passed to the next invocation with the i+1 -th item.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-set"></a>set

**At a glance:** Returns: nothing

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- set

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: nothing
- The set operator assigns a source channel to a variable, whose name is specified as a closure parameter:
- Using set is semantically equivalent to assigning a variable:
- See also: tap

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitcsv"></a>splitCsv

**At a glance:** Returns: channel

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- splitCsv

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The splitCsv operator parses and splits CSV files or text from a source channel into records.
- For example:
- The above example shows hows CSV text is parsed and split into individual rows, where each row is simply a list of columns.
- When the CSV begins with a header line defining the column names, and the header option is true , each row is returned as a map instead:
- The header option can also just be a list of columns:
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitfasta"></a>splitFasta

**At a glance:** Returns: channel

**Summary:** 11 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- splitFasta

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The splitFasta operator splits FASTA files or text from a source channel into individual sequences.
- The by option can be used to group sequences into chunks of a given size.
- The following example shows how to read a FASTA file and split it into chunks of 10 sequences each:
- The record option can be used to split FASTA content into records instead of text chunks.
- Each record is a map that allows you to access the FASTA sequence data with ease.
- For example:
- The above example loads the misc/sample.fa file, splits it into records containing the id and seqString fields (i.e.
- the sequence id and the sequence data), filters records by their ID, and finally prints the sequence string of each record.
- Available options:
- See also: countFasta

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitfastq"></a>splitFastq

**At a glance:** Returns: channel

**Summary:** 10 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- splitFastq

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The splitFastq operator splits FASTQ files or text from a source channel into individual sequences.
- The by option can be used to group sequences into chunks of a given size.
- The following example shows how to read a FASTQ file and split it into chunks of 10 sequences each:
- The record option can be used to split FASTQ content into records instead of text chunks.
- Each record is a map that allows you to access the FASTQ sequence data with ease.
- For example:
- The pe option can be used to split paired-end FASTQ files.
- Available options:
- See also: countFastq

#### Constraints
- The source channel must emit tuples containing the file pairs.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitjson"></a>splitJson

**At a glance:** Returns: channel

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- splitJson

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The splitJson operator splits JSON files or text from a source channel into individual records.
- If the source item is a JSON array, each element of the array will be emitted:
- If the source item is a JSON object, each key-value pair will be emitted as a map with the properties key and value :
- The path option can be used to query a section of the JSON document to parse and split:
- Available options:
- See also: countJson

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splittext"></a>splitText

**At a glance:** Returns: channel

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- splitText

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The splitText operator splits multi-line text content from a source channel into chunks of N lines:
- The above example loads a collection of text files, splits the content of each file into individual lines, and prints each line.
- The by option can be used to emit chunks of N lines:
- An optional closure can be used to transform each text chunk produced by the operator.
- The following example shows how to split text files into chunks of 10 lines and transform them to uppercase letters:
- Available options:
- See also: countLines

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-subscribe"></a>subscribe

**At a glance:** Returns: nothing

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- subscribe

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: nothing
- The subscribe operator invokes a custom function for each item from a source channel:
- The subscribe operator supports multiple types of event handlers:
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-sum"></a>sum

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- sum

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The sum operator emits the sum of all items in a source channel:
- An optional closure can be used to transform each item before it is added to the sum:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-take"></a>take

**At a glance:** Returns: channel

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- take

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The take operator takes the first N items from a source channel:
- See also: until

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tap"></a>tap

**At a glance:** Returns: channel

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- tap

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The tap operator assigns a source channel to a variable, and emits the source channel.
- It is a useful way to extract intermediate output channels from a chain of operators.
- For example:
- See also: set

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tointeger"></a>toInteger

**At a glance:** Returns: channel

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- toInteger

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The toInteger operator converts string values from a source channel to integer values:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tolist"></a>toList

**At a glance:** Returns: dataflow value

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- toList

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The toList operator collects all the items from a source channel into a list and emits the list as a single item:
- See also: collect

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tosortedlist"></a>toSortedList

**At a glance:** Returns: dataflow value

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- toSortedList

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: dataflow value
- The toSortedList operator collects all the items from a source channel into a sorted list and emits the list as a single item:
- An optional closure can be used to control how items are compared when sorting.
- For example, to sort tuples by their second element in descending order:
- See also: collect

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-transpose"></a>transpose

**At a glance:** Returns: channel

**Summary:** 7 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- transpose

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The transpose operator atransposesa each tuple from a source channel by flattening any nested list in each tuple, emitting each nested item separately.
- To be more precise, the operator transforms a sequence of tuples like (K, list(V), list(W), ..) into a sequence of tuples like (K, V, W, ..) .
- For example:
- The remainder option can be used to emit any incomplete items:
- Available options:
- See also: groupTuple

#### Constraints
- If each source item has more than two elements, these will be flattened by the first element in the item, and a new item will be emitted only when it is complete:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-unique"></a>unique

**At a glance:** Returns: channel

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- unique

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The unique operator emits the unique items from a source channel:
- An optional closure can be used to transform each item before it is evaluated for uniqueness:
- See also: distinct

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-until"></a>until

**At a glance:** Returns: channel

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- until

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The until operator emits each item from a source channel until a stopping condition is satisfied:
- See also: take

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-view"></a>view

**At a glance:** Returns: channel

**Summary:** 15 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- view

#### Source
- https://www.nextflow.io/docs/stable/reference/operator.html
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Returns: channel
- The view operator prints each item from a source channel to standard output:
- An optional closure can be used to transform each item before it is printed:
- The view operator also emits every item that it receives, allowing it to be chained with other operators.
- Available options:
- View a projectas script file(s).
- Usage
- Description
- The view command is used to inspect the pipelines that are already stored in the global nextflow cache.
- For downloading a pipeline into the global cache ~/.nextflow/assets , refer to the pull command.
- Options
- Examples
- Viewing the contents of a downloaded pipeline.
- List the folder structure of the downloaded pipeline:
- View the contents of a downloaded pipeline without omitting the header:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## CLI

### <a id="cli-config"></a>Config

**At a glance:** Print the resolved pipeline configuration.

**Summary:** 15 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- config
- Executor-specific configuration

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- Print the resolved pipeline configuration.
- Usage
- Description
- The config command is used for printing the projectas configuration i.e.
- the nextflow.config and is especially useful for understanding the resolved profiles and parameters that Nextflow will use run a pipeline.
- For in-depth information, please refer the Config profiles section.
- Options
- Examples
- Print out the inferred config using a the default group key-value notation.
- Print out the config using a flat notation.
- Print out the config using the Java properties notation.
- Print out the value of a specific configuration property.
- Print out all profiles from the projectas configuration.
- Executor config settings can be applied to specific executors by prefixing the executor name with the symbol $ and using it as special scope.
- For example:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-auth"></a>auth

**At a glance:** Manage Seqera Platform authentication.

**Summary:** 16 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- auth

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Manage Seqera Platform authentication.
- Usage
- Description
- The auth command provides authentication and configuration management for Seqera.
- For Seqera Cloud, it uses an OAuth2 authentication flow to generate and save a Personal Access Token (PAT) locally.
- For Seqera Enterprise installations, it uses direct PAT authentication.
- Credentials are saved to ~/.nextflow/seqera-auth.config .
- An includeConfig statement is automatically added to ~/.nextflow/config or the configuration file set using $NXF_HOME .
- Options
- Subcommands
- Examples
- Authenticate with Seqera Cloud:
- Authenticate with an Enterprise installation:
- View current authentication status:
- Configure Seqera settings:
- Remove authentication:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-clean"></a>clean

**At a glance:** Clean up cache and work directories.

**Summary:** 15 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- clean

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Clean up cache and work directories.
- Usage
- Description
- Upon invocation within a directory, nextflow creates a project specific .nextflow.log file, .nextflow cache directory as well as a work directory.
- The clean command is designed to facilitate removal of these files from previous executions.
- A list of run names and session ids can be generated by invoking nextflow log -q .
- If no run name or session id is provided, it will clean the latest run.
- Options
- Examples
- Dry run to remove work directories for the run name boring_euler :
- Remove work directories for the run name boring_euler .
- Remove the execution entries except for a specific execution.
- Dry run to remove the execution data before a specific execution.
- Dry run to remove the execution data after a specific execution.
- Dry run to remove the temporary execution data for a specific execution, while keeping the log files.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-clone"></a>clone

**At a glance:** Clone a remote project into a folder.

**Summary:** 9 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- clone

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Clone a remote project into a folder.
- Usage
- Description
- The clone command downloads a pipeline from a Git-hosting platform into the current directory and modifies it accordingly.
- For downloading a pipeline into the global cache ~/.nextflow/assets , please refer to the nextflow pull command.
- Options
- Examples
- Clone the latest revision of a pipeline.
- Clone a specific revision of a pipeline.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-commands"></a>Commands

**At a glance:** Reference for Commands.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Commands

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-console"></a>console

**At a glance:** Launch the Nextflow interactive console.

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- console

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Launch the Nextflow interactive console.
- Usage
- Description
- The console command provides a Graphical User Interface (GUI) and an interactive REPL (Read-Eval-Print-Loop) for quick experimentation.
- Options
- None available
- Examples
- Launch the console GUI.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-drop"></a>drop

**At a glance:** Delete the local copy of a project.

**Summary:** 9 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- drop

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Delete the local copy of a project.
- Usage
- Description
- The drop command is used to remove the projects which have been downloaded into the global cache.
- Please refer the list command for generating a list of downloaded pipelines.
- Options
- Examples
- Drop the nextflow-io/hello project.
- Forcefully drop the nextflow-io/hello pipeline, ignoring any local changes.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-fs"></a>fs

**At a glance:** Perform basic filesystem operations.

**Summary:** 14 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fs

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Perform basic filesystem operations.
- Usage
- Description
- The fs command is used to perform filesystem operations like copy, move, delete, list directory, etc.
- Like the file() method, it can work with local files, remote URLs, and remote object storage.
- Storage credentials can be provided through the same manner as launching a pipeline (Nextflow config, environment vars, etc).
- Options
- Examples
- List a directory.
- Print the contents of a file to standard output.
- Copy a file or directory.
- Move a file or directory.
- Delete a file or directory.
- Print file or directory attributes.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-help"></a>help

**At a glance:** Print the top-level help or specific help for a command.

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- help

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Print the top-level help or specific help for a command.
- Usage
- Description
- The help command prints out the overview of the CLI interface and enumerates the top-level options and commands .
- Note that this command is equivalent to simply invoking nextflow at the command line.
- Options
- Examples
- Invoke the help option for the drop command.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-info"></a>info

**At a glance:** Print project or system runtime information.

**Summary:** 10 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- info

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Print project or system runtime information.
- Usage
- Description
- The info command prints out the nextflow runtime information about the hardware as well as the software versions of the Nextflow version and build, operating system, and Groovy and Java runtime.
- It can also be used to display information about a specific project.
- If no run name or session id is provided, it will clean the latest run.
- Options
- Examples
- Display Nextflow runtime and system info:
- Display information about a specific project:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-inspect"></a>inspect

**At a glance:** Inspect process settings in a pipeline project.

**Summary:** 9 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- inspect

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Inspect process settings in a pipeline project.
- Usage
- Description
- The inspect command allows you to determine the container for each process in a pipeline without running the pipeline.
- It prints to stdout a listing of containers for each process, formatted either as JSON or Nextflow configuration.
- Options
- Examples
- Get the list of containers used by a pipeline.
- Specify parameters as with the run command:

#### Constraints
- Currently only supports the container directive.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-kuberun"></a>kuberun

**At a glance:** Launch a Nextflow pipeline on a Kubernetes cluster.

**Summary:** 12 explanations, 0 constraints, 37 allowed elements, 0 examples.

#### Related Terms
- kuberun

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Launch a Nextflow pipeline on a Kubernetes cluster.
- Usage
- Description
- The kuberun command builds upon the run command and offers a deep integration with the Kubernetes execution environment.
- This command deploys the Nextflow runtime as a Kubernetes pod and assumes that you've already installed the kubectl CLI.
- The kuberun command does not allow the execution of local Nextflow scripts.
- See Kubernetes for more information.
- Options
- The kuberun command supports the following options from run :
- The following new options are also available:
- Examples
- Execute a pipeline into a Kubernetes cluster.

#### Allowed Elements
- -cache
- -disable-jobs-cancellation
- -dsl1
- -dsl2
- -dump-channels
- -dump-hashes
- -e.<key>=<value>
- -entry
- -h, -help
- -hub
- -latest
- -main-script
- -name
- -offline
- -params-file
- -plugins
- -preview
- -process.<key>=<value>
- -profile
- -qs, -queue-size
- -resume
- -r, -revision
- -stub, -stub-run
- -user
- -with-conda
- -with-dag
- -N, -with-notification
- -with-report
- -with-spack
- -with-timeline
- -with-tower
- -with-trace
- -with-wave
- -with-weblog
- -without-spack
- -without-wave
- -w, -work-dir

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-launch"></a>launch

**At a glance:** Launch a workflow in Seqera Platform .

**Summary:** 8 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- launch

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Launch a workflow in Seqera Platform .
- Usage
- Description
- The launch command launches a pipeline run in Seqera Platform.
- To log in and configure the execution environment, use the auth command.
- Options
- Examples
- Execute a pipeline in Seqera Platform.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-lineage"></a>lineage

**At a glance:** Inspect lineage metadata for Nextflow runs.

**Summary:** 9 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- lineage

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- Inspect lineage metadata for Nextflow runs.
- Usage
- Description
- The lineage command is used to inspect lineage metadata.
- See the Getting started with data lineage guide to learn how to get started with data lineage.
- Options
- Subcommands
- The lineage scope controls the generation of lineage metadata.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-lint"></a>lint

**At a glance:** Lint Nextflow scripts and config files.

**Summary:** 10 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- lint

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Lint Nextflow scripts and config files.
- Usage
- Description
- The lint command parses and analyzes the given Nextflow scripts and config files, formats them if specified, and prints any errors.
- Directories are recursively scanned for scripts and config files to lint.
- Options
- Examples
- Lint a specific file.
- Lint all files in the current directory (and subdirectories) with concise output.
- Lint and format all files in the current directory (and subdirectories) and use two spaces per indent.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-list"></a>list

**At a glance:** List all downloaded projects.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- list

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- List all downloaded projects.
- Usage
- Description
- The list commands prints a list of the projects which are already downloaded into the global cache ~/.nextflow/assets .
- Options
- Examples
- List the downloaded pipelines.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-log"></a>log

**At a glance:** Print the execution history and log information.

**Summary:** 15 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- log

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Print the execution history and log information.
- Usage
- Description
- The log command is used to query the execution metadata associated with pipelines executed by Nextflow.
- The list of executed pipelines can be generated by running nextflow log .
- Instead of run name, it's also possible to use a session id.
- Moreover, this command contains multiple options to facilitate the queries and is especially useful while debugging a pipeline and while inspecting pipeline execution metadata.
- Options
- Examples
- Listing the execution logs of previous invocations of all pipelines in a project.
- List the execution entries after a specific execution.
- List the execution entries before a specific execution.
- List the execution entries except for a specific execution.
- Filter specific fields from the execution log of a process.
- Filter fields from the execution log of a process based on a criteria.

#### Constraints
- Listing only the run names of the execution logs of all pipelines invocations in a project.
- List the execution entries only a specific execution.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-options"></a>Options

**At a glance:** The top-level options are meant to be invoked in relation to the core Nextflow application and are applied to all commands.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Options

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- The top-level options are meant to be invoked in relation to the core Nextflow application and are applied to all commands.
- For options specific to any command, refer the CLI Commands section.
- Available options:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-plugin"></a>plugin

**At a glance:** Manage plugins and run plugin-specific commands.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- plugin

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Manage plugins and run plugin-specific commands.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-pull"></a>pull

**At a glance:** Download or update a project.

**Summary:** 10 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- pull

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Download or update a project.
- Usage
- Description
- The pull command downloads a pipeline from a Git-hosting platform into the global cache ~/.nextflow/assets and modifies it accordingly.
- For downloading a pipeline into a local directory, please refer to the nextflow clone command.
- Options
- Examples
- Download a new pipeline or pull the latest revision for a specific project.
- Pull the latest revision for all downloaded projects.
- Download a specific revision of a new project or pull the latest revision for a specific project.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-run"></a>run

**At a glance:** Execute a pipeline.

**Summary:** 6 explanations, 0 constraints, 7 allowed elements, 0 examples.

#### Related Terms
- run

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Execute a pipeline.
- Usage
- Description
- The run command is used to execute a local pipeline script or remote pipeline project.
- Options
- Examples

#### Allowed Elements
- Run a specific revision of a remote pipeline. $ nextflow run nextflow-io/hello -r v1.1 N E X T F L O W ~ version 20.07.1 Launching `nextflow-io/hello` [grave_cajal] - revision: 1c3e9e7404 [v1.1]
- Choose a profile for running the project. Assumes that a profile named docker has already been defined in the config file. $ nextflow run main.nf -profile docker
- Execute a pipeline and generate the summary HTML report. For more information on the metrics, please refer the Reports section: $ nextflow run main.nf -with-report
- Execute a pipeline with a custom queue size. By default, the queue size is the number of available CPUs. $ nextflow run nextflow-io/hello -qs 4
- Invoke the pipeline with a specific workflow as the entry-point. $ nextflow run main.nf -entry workflow_A
- Execute a pipeline with integrated monitoring in Seqera Platform . $ nextflow run nextflow-io/hello -with-tower
- Execute a pipeline with a custom parameters file (YAML or JSON). $ nextflow run main.nf -params-file pipeline_params.yml See Pipeline parameters for more information about writing custom parameters files.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-secrets"></a>secrets

**At a glance:** Manage pipeline secrets .

**Summary:** 5 explanations, 0 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- secrets

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Manage pipeline secrets .
- Usage
- Options
- Subcommands
- Examples

#### Allowed Elements
- Set a secret: $ nextflow secrets set FOO "Hello world"
- List secrets: $ nextflow secrets list
- Get a secret: $ nextflow secrets get FOO
- Delete a secret: $ nextflow secrets delete FOO

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-self-update"></a>self-update

**At a glance:** Update the nextflow runtime to the latest available version.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- self-update

#### Source
- https://www.nextflow.io/docs/stable/reference/cli.html

<details>
<summary>Show full details</summary>

#### Explanation
- Update the nextflow runtime to the latest available version.
- Usage
- Description
- The self-update command directs the nextflow CLI to update itself to the latest stable release.
- Examples
- Update Nextflow.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Config

### <a id="config-apptainer"></a>apptainer

**At a glance:** The apptainer scope controls how Apptainer containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- apptainer

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The apptainer scope controls how Apptainer containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-aws"></a>aws

**At a glance:** The aws scope controls the interactions with AWS, including AWS Batch and S3.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- aws

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The aws scope controls the interactions with AWS, including AWS Batch and S3.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-azure"></a>azure

**At a glance:** The azure scope allows you to configure the interactions with Azure, including Azure Batch and Azure Blob Storage.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- azure

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The azure scope allows you to configure the interactions with Azure, including Azure Batch and Azure Blob Storage.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-charliecloud"></a>charliecloud

**At a glance:** The charliecloud scope controls how Charliecloud containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- charliecloud

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The charliecloud scope controls how Charliecloud containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-dag"></a>dag

**At a glance:** The dag scope controls the workflow diagram generated by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- dag

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The dag scope controls the workflow diagram generated by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-docker"></a>docker

**At a glance:** The docker scope controls how Docker containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- docker

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The docker scope controls how Docker containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-env"></a>env

**At a glance:** The env scope allows the definition one or more variables that will be exported into the environment where workflow tasks are executed.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- env

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The env scope allows the definition one or more variables that will be exported into the environment where workflow tasks are executed.
- Simply prefix your variable names with the env scope or surround them by curly brackets, as shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-executor-specific-defaults"></a>Executor-specific defaults

**At a glance:** Some executor settings have different default values depending on the executor.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Executor-specific defaults

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- Some executor settings have different default values depending on the executor.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-fusion"></a>fusion

**At a glance:** The fusion scope provides advanced configuration for the use of the Fusion file system .

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- fusion

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The fusion scope provides advanced configuration for the use of the Fusion file system .
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-google"></a>google

**At a glance:** The google scope allows you to configure the interactions with Google Cloud, including Google Cloud Batch and Google Cloud Storage.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- google

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The google scope allows you to configure the interactions with Google Cloud, including Google Cloud Batch and Google Cloud Storage.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-java-settings"></a>Java settings

**At a glance:** Reference for Java settings.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Java settings

#### Source
- https://www.nextflow.io/docs/stable/reference/env-vars.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-k8s"></a>k8s

**At a glance:** The k8s scope controls the deployment and execution of workflow applications in a Kubernetes cluster.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- k8s

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The k8s scope controls the deployment and execution of workflow applications in a Kubernetes cluster.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-mail"></a>mail

**At a glance:** The mail scope controls the mail server used to send email notifications.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- mail

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The mail scope controls the mail server used to send email notifications.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-manifest"></a>manifest

**At a glance:** The manifest scope allows you to define some metadata that is useful when publishing or running your pipeline.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- manifest

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The manifest scope allows you to define some metadata that is useful when publishing or running your pipeline.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-nextflow"></a>nextflow

**At a glance:** Reference for nextflow.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- nextflow

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-nextflow-settings"></a>Nextflow settings

**At a glance:** Reference for Nextflow settings.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Nextflow settings

#### Source
- https://www.nextflow.io/docs/stable/reference/env-vars.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-notification"></a>notification

**At a glance:** The notification scope controls the automatic sending of an email notification on workflow completion.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- notification

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The notification scope controls the automatic sending of an email notification on workflow completion.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-other-settings"></a>Other settings

**At a glance:** Reference for Other settings.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Other settings

#### Source
- https://www.nextflow.io/docs/stable/reference/env-vars.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-podman"></a>podman

**At a glance:** The podman scope controls how Podman containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- podman

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The podman scope controls how Podman containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-report"></a>report

**At a glance:** The report scope allows you to configure the workflow Execution report .

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- report

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The report scope allows you to configure the workflow Execution report .
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-sarus"></a>sarus

**At a glance:** The sarus scope controls how Sarus containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- sarus

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The sarus scope controls how Sarus containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-seqera-platform-settings"></a>Seqera Platform settings

**At a glance:** Reference for Seqera Platform settings.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Seqera Platform settings

#### Source
- https://www.nextflow.io/docs/stable/reference/env-vars.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-shifter"></a>shifter

**At a glance:** The shifter scope controls how Shifter containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- shifter

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The shifter scope controls how Shifter containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-singularity"></a>singularity

**At a glance:** The singularity scope controls how Singularity containers are executed by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- singularity

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The singularity scope controls how Singularity containers are executed by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-timeline"></a>timeline

**At a glance:** The timeline scope controls the execution timeline report generated by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- timeline

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The timeline scope controls the execution timeline report generated by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-tower"></a>tower

**At a glance:** The tower scope controls the settings for Seqera Platform (formerly Tower Cloud).

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- tower

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The tower scope controls the settings for Seqera Platform (formerly Tower Cloud).
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-trace"></a>trace

**At a glance:** The trace scope controls the layout of the execution trace file generated by Nextflow.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- trace

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The trace scope controls the layout of the execution trace file generated by Nextflow.
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-unscoped-options"></a>Unscoped options

**At a glance:** Reference for Unscoped options.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Unscoped options

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-wave"></a>wave

**At a glance:** The wave scope provides advanced configuration for the use of Wave containers .

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- wave

#### Source
- https://www.nextflow.io/docs/stable/reference/config.html

<details>
<summary>Show full details</summary>

#### Explanation
- The wave scope provides advanced configuration for the use of Wave containers .
- The following settings are available:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Types

### <a id="types-channel"></a>Channel

**At a glance:** A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of values of type E .

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Channel<E>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of values of type E .
- It is used to facilitate dataflow logic in a workflow.
- See Dataflow for an overview of dataflow types.
- See Operators for the available methods for channels.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-bage"></a>Bag<E>

**At a glance:** Implements the Iterable<E> trait.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Bag<E>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- Implements the Iterable<E> trait.
- A bag is an unordered collection of values of type E .
- The following operations are supported for bags:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-boolean"></a>Boolean

**At a glance:** Reference for Boolean.

**Summary:** 3 explanations, 0 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Boolean

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A boolean literal can be true or false :
- A boolean can be true or false .
- The following operations are supported for booleans:

#### Allowed Elements
- && : logical AND
- || : logical OR
- ! : logical NOT

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-duration"></a>Duration

**At a glance:** A Duration represents a duration of time with millisecond precision.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Duration

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A Duration represents a duration of time with millisecond precision.
- A Duration can be created by adding a unit suffix to an integer (e.g.
- 1.h ), or by explicitly casting to Duration :
- The following suffixes are available:
- Durations can be compared like numbers, and they support basic arithmetic operations:
- The following methods are available for a Duration:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-float"></a>Float

**At a glance:** A float is a floating-point number (i.e.

**Summary:** 3 explanations, 0 constraints, 2 allowed elements, 0 examples.

#### Related Terms
- Float

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A float is a floating-point number (i.e.
- real number) that can be positive or negative.
- The following operations are supported for floats:

#### Allowed Elements
- +, -, *, / : addition, subtraction, multiplication, division
- ** : exponentation

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-integer"></a>Integer

**At a glance:** An integer is a whole number that can be positive or negative.

**Summary:** 2 explanations, 0 constraints, 5 allowed elements, 0 examples.

#### Related Terms
- Integer

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- An integer is a whole number that can be positive or negative.
- The following operations are supported for integers:

#### Allowed Elements
- +, -, *, / : addition, subtraction, multiplication, integer division
- % : remainder of integer division (i.e. modulus)
- ** : exponentation
- & , | , ^ , ~ : bitwise AND, OR, XOR, NOT
- << , >> : left and right bit-shift

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-iterablee"></a>Iterable<E>

**At a glance:** Implemented by the following types: Bag<E> , List<E> , Set<E>

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Iterable<E>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- Implemented by the following types: Bag<E> , List<E> , Set<E>
- Iterable is a trait implemented by collection types that support iteration.
- Types that implement Iterable can be passed as an Iterable parameter of a method, and they can use all of the methods described below.
- The following methods are available for iterables:
- toUnique( comparator: (E) -> R ) -> Iterable<E>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-liste"></a>List<E>

**At a glance:** Implements the Iterable<E> trait.

**Summary:** 5 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- List<E>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- Implements the Iterable<E> trait.
- A list is an ordered collection of values of type E .
- See Lists for an overview of lists.
- The following operations are supported for lists:
- The following methods are available for a list:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-mapkv"></a>Map<K,V>

**At a glance:** A map associates or maps keys of type K to values of type V .

**Summary:** 4 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Map<K,V>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A map associates or maps keys of type K to values of type V .
- See Maps for an overview of maps.
- The following operations are supported for maps:
- The following methods are available for a map:

#### Constraints
- Each key can map to at most one value a a map cannot contain duplicate keys.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-memoryunit"></a>MemoryUnit

**At a glance:** A MemoryUnit represents a quantity of bytes.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- MemoryUnit

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A MemoryUnit represents a quantity of bytes.
- A MemoryUnit can be created by adding a unit suffix to an integer (e.g.
- 1.GB ), or by explicitly casting to MemoryUnit :
- The following suffixes are available:
- Memory units can be compared like numbers, and they support basic arithmetic operations:
- The following methods are available for a MemoryUnit object:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-operations"></a>Operations

**At a glance:** A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, and object storage paths (e.g.

**Summary:** 12 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Operations

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, and object storage paths (e.g.
- Amazon S3).
- The file() function can be used to get a Path for a given filename or URL:
- The files() function can be used to get a collection of Paths from a glob pattern:
- The following sections describe the methods that are available for paths.
- The following operations are supported for paths:
- The following methods are useful for getting attributes of a path:
- The following methods are available for reading files:
- The following methods are available for writing to files:
- The following methods are available for manipulating files and directories in a filesystem:
- The following methods are available for listing and traversing directories:
- The following methods are available for splitting and counting the records in files:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-sete"></a>Set<E>

**At a glance:** Implements the Iterable<E> trait.

**Summary:** 4 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Set<E>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- Implements the Iterable<E> trait.
- A set can be created from a list using the toSet() method:
- The following operations are supported for sets:
- The following methods are available for a set:

#### Constraints
- A set is an unordered collection of values of type E which cannot contain duplicates.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-string"></a>String

**At a glance:** Reference for String.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- String

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A string literal consists of arbitrary text enclosed by single or double quotes:
- A triple-quoted string can span multiple lines:
- A slashy string is enclosed by slashes instead of quotes:
- A string is an immutable sequence of characters.
- See Strings for an overview of strings.
- The following operations are supported for strings:
- The following methods are available for a string:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-tuple"></a>Tuple

**At a glance:** A tuple is a fixed sequence of values, where each value can have its own type.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Tuple

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A tuple is a fixed sequence of values, where each value can have its own type.
- Tuples can be created using the tuple function.
- The following operations are supported for tuples:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-valuev"></a>Value<V>

**At a glance:** A dataflow value (also known as a value channel ) is an asynchronous value of type V .

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Value<V>

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A dataflow value (also known as a value channel ) is an asynchronous value of type V .
- It is used to facilitate dataflow logic in a workflow.
- See Dataflow for an overview of dataflow types.
- The following methods are available for a dataflow value:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-versionnumber"></a>VersionNumber

**At a glance:** A VersionNumber represents a semantic or calendar version number.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- VersionNumber

#### Source
- https://www.nextflow.io/docs/stable/reference/stdlib-types.html

<details>
<summary>Show full details</summary>

#### Explanation
- A VersionNumber represents a semantic or calendar version number.
- The following methods are available for a VersionNumber:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Script Language

### <a id="script-language-process"></a>Process

**At a glance:** A process consists of a name and a body.

**Summary:** 10 explanations, 3 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Process
- Process (typed)

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A process consists of a name and a body.
- The process body consists of one or more statements .
- A process may define additional sections for directives , inputs , outputs , script , exec , and stub :
- Each section may contain one or more statements.
- See Process reference for the set of available input qualifiers, output qualifiers, and directives.
- The script section can be substituted with an exec section:
- See Processes for more information on the semantics of each process section.
- A typed process is a process that uses static types for inputs and/or outputs:
- Typed processes may specify the following sections:
- See Processes (typed) for more information on the semantics of typed processes.

#### Constraints
- A minimal process definition must return a string:
- For directives, inputs, and outputs, these statements must be function calls .
- The script and stub sections must return a string in the same manner as a function .

#### Allowed Elements
- A process must define a script or exec section (see below). All other sections are optional. Directives do not have an explicit section label, but must be defined first.
- The script: section label can be omitted only when there are no other sections in the body.
- Sections must be defined in the order shown above, with the exception of the output section, which can also be specified after the script and stub.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-function"></a>Function

**At a glance:** Reference for Function.

**Summary:** 11 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Function
- Function call

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A function consists of a name, parameter list, and a body:
- The function body consists of one or more statements .
- The last statement is implicitly treated as a return statement if it is an expression statement that returns a value.
- The return statement can be used to explicitly return from a function:
- A function call consists of a name and argument list:
- A method call consists of an object expression and a function call separated by a dot , spread dot , or safe dot :
- The argument list may contain any number of positional arguments and named arguments :
- The named arguments are collected into a map and provided as the first positional argument to the function.
- The above function call can be rewritten as:
- The parentheses can be omitted when the function call is also an expression statement and there is at least one argument:
- If the last argument is a closure, it can be specified outside of the parentheses:

#### Constraints
- The argument name must be an identifier or string literal.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-enum"></a>Enum

**At a glance:** An enum type declaration consists of a name and a body.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Enum type

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An enum type declaration consists of a name and a body.
- The body consists of a comma-separated list of identifiers:
- Enum values in the above example can be accessed as Day.MONDAY , Day.TUESDAY , and so on.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-variable"></a>Variable

**At a glance:** Reference for Variable declaration.

**Summary:** 10 explanations, 3 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Variable declaration
- Variable

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Variables can be declared with the def keyword:
- Multiple variables can be declared in a single statement if the initializer is a list literal with the same number of elements and declared variables:
- Each variable has a scope , which is the region of code in which the variable can be used.
- Variables declared in a function, as well as the parameters of that function, exist for the duration of that function call.
- The same applies to closures.
- Workflow inputs exist for the entire workflow body.
- Variables declared in the main section exist for the main, emit, and publish sections.
- Named outputs are not considered variable declarations and therefore do not have any scope.
- Process input variables exist for the entire process body.
- A variable expression is a reference to a variable or other named value:

#### Constraints
- Variables declared in the process script, exec, and stub sections exist only in their respective section, with one exception a variables declared without the def keyword also exist in the output section.
- Variables declared in an if or else branch exist only within that branch:
- A variable cannot be declared with the same name as another variable in the same scope or an enclosing scope:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-assignment"></a>Assignment

**At a glance:** Reference for Assignment.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Assignment

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An assignment statement consists of a target expression and a source expression separated by an equals sign:
- The source expression can be any expression.
- Multiple variables can be assigned in a single statement as long as the source expression is a list literal with the same number of elements and assigned variables:

#### Constraints
- The target expression must be a variable , index , or property expression.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-include"></a>Include

**At a glance:** Reference for Include.

**Summary:** 7 explanations, 2 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Include

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An include declaration consists of an include source and one or more include clauses :
- ./module.nf ) or a plugin (e.g.
- plugin/nf-hello ).
- In the above example, hallo is included under the alias sayHello .
- Include clauses can be separated by semi-colons or newlines:
- Include clauses can also be specified as separate includes:
- The following definitions can be included:

#### Constraints
- The include source should be a string literal and should refer to either a local path (e.g.
- Each include clause should specify a name, and may also specify an alias .

#### Allowed Elements
- Functions
- Processes
- Named workflows

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-feature-flag"></a>Feature flag

**At a glance:** A feature flag declaration is an assignment.

**Summary:** 2 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Feature flag

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A feature flag declaration is an assignment.
- number, string, boolean):

#### Constraints
- The target should be a valid feature flag and the source should be a literal (i.e.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-shebang"></a>Shebang

**At a glance:** Reference for Shebang.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Shebang

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- The first line of a script can be a shebang :

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-assert"></a>assert

**At a glance:** Reference for assert.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- assert

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An assert statement consists of the assert keyword followed by a boolean expression, with an optional error message separated by a colon:
- If the condition is false, an error will be raised with the given error message.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-binary-expressions"></a>Binary expressions

**At a glance:** Reference for Binary expressions.

**Summary:** 2 explanations, 0 constraints, 31 allowed elements, 0 examples.

#### Related Terms
- Binary expressions

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A binary expression consists of a left expression and a right expression separated by a binary operator :
- The following binary operators are available:

#### Allowed Elements
- ** : power (i.e. exponentiation)
- * : multiplication
- / : division
- % : remainder (i.e. modulo)
- + : addition
- - : subtraction
- << : left shift
- >> : right shift
- >>> : unsigned right shift
- .. : inclusive range
- ..< : right-exclusive range
- as : type cast
- instanceof : type relation
- !instanceof : negated type relation
- < : less than
- > : greater than
- <= : less than or equals
- >= : greater than or equals
- in : membership
- !in : negated membership
- == : equals
- != : negated equals
- <=> : spaceship (i.e. three-way comparison)
- =~ : regex find
- ==~ : regex match
- & : bitwise AND
- ^ : bitwise XOR (exclusive or)
- | : bitwise OR
- && : logical AND
- || : logical OR
- ?: elvis (i.e. short ternary)

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-capturing-groups"></a>Capturing groups

**At a glance:** You can match a pattern that includes groups.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Capturing groups

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- You can match a pattern that includes groups.
- First create a matcher object with the =~ operator.
- Then, you can index the matcher object to find the matches: matcher[0] returns a list representing the first match of the regular expression in the string.
- The first list element is the string that matches the entire regular expression, and the remaining elements are the strings that match each group.
- Hereas how it works:
- Applying some syntactic sugar, you can do the same in just one line of code:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-closure"></a>Closure

**At a glance:** Reference for Closure.

**Summary:** 5 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Closure

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A closure, also known as an anonymous function, consists of a parameter list followed by zero or more statements, enclosed in curly braces:
- The above closure takes two arguments and returns their sum.
- The closure body is identical to that of a function .
- Closures can access variables outside of their scope:
- See standard library and operator for more examples of how closures are used in practice.

#### Constraints
- Statements should be separated by newlines or semi-colons, and the last statement is implicitly treated as a return statement :
- Closures can declare local variables that exist only for the lifetime of each closure invocation:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-closures"></a>Closures

**At a glance:** A closure is a function that can be used like a regular value.

**Summary:** 16 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Closures

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- A closure is a function that can be used like a regular value.
- Typically, closures are passed as arguments to higher-order functions to express computations in a declarative manner.
- For example:
- The above example defines a closure, which takes one parameter named v and returns the square of v ( v * v ).
- The closure is assigned to the variable square .
- square can now be called like a function:
- The above example prints 81 .
- The main use case for a closure is as an argument to a higher-order function:
- The collect method of a list applies a mapping function to each value in the list and produces a new list.
- The above example produces:
- The example can be expressed more concisely as:
- Another example is the each method of a map, which takes a closure with two arguments corresponding to the key and value of each map entry:
- Prints:
- Closures can access variables outside of their scope:
- While the each method is a convenient way to iterate through a collection and build up some result, a more idiomatic way to do this is to use the inject method:
- This way, the closure is fully self-contained because it doesn't access or mutate any variables outside of its scope.

#### Constraints
- A closure can also declare local variables that exist only for the lifetime of each closure invocation:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-comments"></a>Comments

**At a glance:** A line comment starts with // and includes the rest of the line.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Comments

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A line comment starts with // and includes the rest of the line.
- A block comment starts with /* and includes all subsequent characters up to the first */ .

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-conditional-execution"></a>Conditional execution

**At a glance:** One of the most important features of any programming language is the ability to execute different code under different conditions.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Conditional execution

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- One of the most important features of any programming language is the ability to execute different code under different conditions.
- This can be done with an if-else statement:
- In some cases, conditional statements can be expressed more concisely as a conditional expression (also known as a ternary expression ):
- A shortened version of the conditional expression can be used to return a value if it is truthy, or fallback to a second value otherwise:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-constructor-call"></a>Constructor call

**At a glance:** Reference for Constructor call.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Constructor call

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A constructor call consists of the new keyword followed by a type name and an argument list enclosed in parentheses:
- If the type is implicitly available in the script, the fully-qualified type name can be elided to the simple type name :
- See Standard library for the set of types that are available in Nextflow scripts.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-deprecations"></a>Deprecations

**At a glance:** Reference for Deprecations.

**Summary:** 1 explanations, 0 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- Deprecations

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- The following legacy features were excluded from this page because they are deprecated:

#### Allowed Elements
- The addParams and params clauses of include declarations. See Module parameters for more information.
- The when: section of a process definition. See When for more information.
- The shell: section of a process definition. See Shell for more information.
- The implicit it closure parameter. See Closures for more information.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-dynamic-string"></a>Dynamic string

**At a glance:** Reference for Dynamic string.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Dynamic string

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Double-quoted strings can be interpolated using the ${} placeholder with an expression:
- If the expression is a name or simple property expression (one or more identifiers separated by dots), the curly braces can be omitted:
- Multi-line double-quoted strings can also be interpolated:
- Single-quoted strings are not interpolated:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-expression-statement"></a>Expression statement

**At a glance:** Any expression can be a statement.

**Summary:** 2 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Expression statement

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Any expression can be a statement.
- println ) or an implicit return statement in a function or closure .

#### Constraints
- In general, the only expressions that can have any effect as expression statements are function calls that have side effects (e.g.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-expressions"></a>Expressions

**At a glance:** An expression represents a value.

**Summary:** 3 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Expressions

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An expression represents a value.
- A literal value is an expression whose value is known at compile-time, such as a number, string, or boolean.
- Every expression has a type , which may be resolved at compile-time or run-time.

#### Constraints
- All other expressions must be evaluated at run-time.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-hello-world"></a>Hello world

**At a glance:** Reference for Hello world.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Hello world

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- You can use the println function to print to the console:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-ifelse"></a>if/else

**At a glance:** An if/else statement consists of an if branch and an optional else branch .

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- if/else

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An if/else statement consists of an if branch and an optional else branch .
- Each branch consists of a boolean expression in parentheses, followed by either a single statement or a block statement (one or more statements in curly braces).
- For example:
- If the condition is true, the if branch will be executed, otherwise the else branch will be executed.
- If/else statements can be chained any number of times by making the else branch another if/else statement:
- A more verbose way to write the same code is:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-index-expression"></a>Index expression

**At a glance:** Reference for Index expression.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Index expression

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- An index expression consists of a left expression and a right expression , with the right expression enclosed in square brackets:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-list"></a>List

**At a glance:** Reference for List.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- List

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A list literal consists of a comma-separated list of zero or more expressions, enclosed in square brackets:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-lists"></a>Lists

**At a glance:** Reference for Lists.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Lists

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Lists are defined using square brackets:
- You can access a given item in the list with square-bracket notation (indexes start at 0):
- In order to get the length of the list use the size method:
- See List<E> for the set of available list operations.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-map"></a>Map

**At a glance:** A map literal consists of a comma-separated list of one or more map entries , enclosed in square brackets.

**Summary:** 7 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Map

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A map literal consists of a comma-separated list of one or more map entries , enclosed in square brackets.
- Each map entry consists of a key expression and value expression separated by a colon:
- An empty map is specified with a single colon to distinguish it from an empty list:
- Both the key and value can be any expression.
- Identifier keys are treated as string literals (i.e.
- the quotes can be omitted).
- A variable can be used as a key by enclosing it in parentheses:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-maps"></a>Maps

**At a glance:** Maps are used to store associative arrays (also known as dictionaries ).

**Summary:** 10 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Maps

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Maps are used to store associative arrays (also known as dictionaries ).
- They are unordered collections of heterogeneous, named data:
- Note that each of the values stored in the map can be of a different type.
- Brett is an integer, Pete is a string, and Andrew is a floating-point number.
- We can access the values in a map in two main ways:
- To add data to or modify a map, the syntax is similar to adding values to list:
- You can also use the + operator to add two maps together:
- When adding two maps, the first map is copied and then appended with the keys from the second map.
- Any conflicting keys are overwritten by the second map.
- See Map<K,V> for the set of available map operations.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-multi-line-strings"></a>Multi-line strings

**At a glance:** Reference for Multi-line strings.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Multi-line strings

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- A block of text that span multiple lines can be defined by delimiting it with triple single or double quotes:
- As in Bash/shell scripts, terminating a line in a multi-line string with a \ character prevents a newline character from separating that line from the one that follows:
- In the preceding example, blastp and its -in , -out , -db and -html switches and their arguments are effectively a single line.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-null"></a>Null

**At a glance:** The null literal is specified as null .

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Null

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- The null literal is specified as null .
- It can be used to represent an empty value:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-number"></a>Number

**At a glance:** A number literal can be an integer or floating-point number, and can be positive or negative.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Number

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A number literal can be an integer or floating-point number, and can be positive or negative.
- Integers can specified in binary with 0b , octal with 0 , or hexadecimal with 0x .
- Floating-point numbers can use scientific notation with the e or E prefix.
- Underscores can be used as thousands separators to make long numbers more readable.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-parentheses"></a>Parentheses

**At a glance:** Reference for Parentheses.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Parentheses

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Any expression can be enclosed in parentheses:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-precedence"></a>Precedence

**At a glance:** Reference for Precedence.

**Summary:** 1 explanations, 0 constraints, 22 allowed elements, 0 examples.

#### Related Terms
- Precedence

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Compound expressions are evaluated in the following order:

#### Allowed Elements
- parentheses
- property expressions
- function calls
- index expressions
- ~ , !
- **
- + , - (unary)
- * , / , %
- + , - (binary)
- << , >>> , >> , .. , ..<
- as
- instanceof , !instanceof
- < , > , <= , >= , in , !in
- == , != , <=>
- =~ , ==~
- &
- ^
- |
- &&
- ||
- ?: (ternary)
- ?: (elvis)

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-property-expression"></a>Property expression

**At a glance:** Reference for Property expression.

**Summary:** 1 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Property expression

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A property expression consists of an object expression and a property , separated by a dot , spread dot , or safe dot :

#### Constraints
- The property must be an identifier or string literal.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-regular-expressions"></a>Regular expressions

**At a glance:** Regular expressions are the Swiss Army knife of text processing.

**Summary:** 4 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Regular expressions

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Regular expressions are the Swiss Army knife of text processing.
- They provide the ability to match and extract patterns from strings.
- Use =~ to check whether a given pattern occurs anywhere in a string:
- Use ==~ to check whether a string matches a given regular expression pattern exactly.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-return"></a>return

**At a glance:** Reference for return.

**Summary:** 2 explanations, 3 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- return

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A return statement consists of the return keyword with an optional expression:
- In the case of a nested closure, the return statement will return from the nearest enclosing closure.

#### Constraints
- Return statements can only be used in functions and closures.
- If a function or closure has multiple return statements (including implicit returns), all of the return statements should either return a value or return nothing.
- If a function or closure does return a value, it should do so for every conditional branch.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-script-declarations"></a>Script declarations

**At a glance:** Reference for Script declarations.

**Summary:** 5 explanations, 0 constraints, 10 allowed elements, 0 examples.

#### Related Terms
- Script declarations

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A Nextflow script may contain the following top-level declarations:
- Script declarations are in turn composed of statements and expressions.
- If there are no script declarations, a script may contain one or more statements , in which case the entire script is treated as an entry workflow.
- For example:
- Is equivalent to:

#### Allowed Elements
- Shebang
- Feature flags
- Include declarations
- Params block
- Parameter declarations (legacy)
- Workflow definitions
- Process definitions
- Function definitions
- Enum types
- Output block

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-script-definitions"></a>Script definitions

**At a glance:** So far, we have been focusing on the basic building blocks of Nextflow code, like variables, lists, strings, and closures.

**Summary:** 7 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Script definitions

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- So far, we have been focusing on the basic building blocks of Nextflow code, like variables, lists, strings, and closures.
- In practice, however, Nextflow scripts are composed of workflows , processes , and functions (collectively known as definitions ), and can include definitions from other scripts.
- To transition a code snippet into a proper workflow script, simply wrap it in a workflow block:
- This block is called the entry workflow .
- It serves as the entrypoint when the script is executed.
- You can also break up code into functions, for example:
- See Workflows , Processes , and Modules for more information about how to use these features in your Nextflow scripts.

#### Constraints
- A script can only have one entry workflow.
- Whenever a script contains only simple statements like println 'Hello!' , Nextflow simply treats it as an entry workflow.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-statements"></a>Statements

**At a glance:** Reference for Statements.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Statements

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- Statements can be separated by either a newline or a semi-colon:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-string-interpolation"></a>String interpolation

**At a glance:** There is an important difference between single-quoted and double-quoted strings: Double-quoted strings support variable interpolations, while single-quoted strings do not.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- String interpolation

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- There is an important difference between single-quoted and double-quoted strings: Double-quoted strings support variable interpolations, while single-quoted strings do not.
- In practice, double-quoted strings can contain the value of an arbitrary variable by prefixing its name with the $ character, or the value of any expression by using the ${expression} syntax, similar to Bash/shell scripts:
- This code prints:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-string-replacement"></a>String replacement

**At a glance:** Reference for String replacement.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- String replacement

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- To replace pattern occurrences in a given string, use the replaceFirst and replaceAll methods:
- To remove part of a string, simply replace it with a blank string:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-strings"></a>Strings

**At a glance:** Reference for Strings.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Strings

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Strings can be defined by enclosing text in single or double quotes ( ' or " characters):
- Strings can be concatenated with + :

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-ternary-expression"></a>Ternary expression

**At a glance:** Reference for Ternary expression.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Ternary expression

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A ternary expression consists of a test expression , a true expression , and a false expression , separated by a question mark and a colon:
- If the test expression is true, the true expression is evaluated, otherwise the false expression is evaluated.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-throw"></a>throw

**At a glance:** Reference for throw.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- throw

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A throw statement consists of the throw keyword followed by an expression that returns an error type:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-trycatch"></a>try/catch

**At a glance:** Reference for try/catch.

**Summary:** 3 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- try/catch

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A try/catch statement consists of a try block followed by any number of catch clauses :
- The try block will be executed, and if an error is raised and matches the expected error type of a catch clause, the code in that catch clause will be executed.
- If no catch clause is matched, the error will be raised to the next enclosing try/catch statement, or to the Nextflow runtime.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-tuples"></a>Tuples

**At a glance:** Tuples are used to store a fixed sequence of heterogeneous values.

**Summary:** 6 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Tuples

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Tuples are used to store a fixed sequence of heterogeneous values.
- They are created using the tuple function:
- Tuple elements are accessed by index:
- Tuples can be destructured in assignments:
- As well as closure parameters:
- See Tuple for the set of available tuple operations.

#### Constraints
- Tuples are immutable a once a tuple is created, its elements cannot be modified.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-unary-expressions"></a>Unary expressions

**At a glance:** Reference for Unary expressions.

**Summary:** 2 explanations, 0 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- Unary expressions

#### Source
- https://www.nextflow.io/docs/stable/reference/syntax.html

<details>
<summary>Show full details</summary>

#### Explanation
- A unary expression consists of a unary operator followed by an expression:
- The following unary operators are available:

#### Allowed Elements
- ~ : bitwise NOT
- ! : logical NOT
- + : unary plus
- - : unary minus

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-variables"></a>Variables

**At a glance:** Reference for Variables.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Variables

#### Source
- https://www.nextflow.io/docs/stable/script.html

<details>
<summary>Show full details</summary>

#### Explanation
- Variables are declared using the def keyword:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Modules

### <a id="modules-multiple-inclusions"></a>Multiple inclusions

**At a glance:** A Nextflow script can include any number of modules, and an include statement can import any number of definitions from a module.

**Summary:** 2 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Multiple inclusions

#### Source
- https://www.nextflow.io/docs/stable/module.html

<details>
<summary>Show full details</summary>

#### Explanation
- A Nextflow script can include any number of modules, and an include statement can import any number of definitions from a module.
- Multiple definitions can be included from the same module by using the syntax shown below:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="modules-sharing-modules"></a>Sharing modules

**At a glance:** Modules are designed to be easy to share and re-use across different pipelines, which helps eliminate duplicate work and spread improvements throughout the community.

**Summary:** 2 explanations, 0 constraints, 3 allowed elements, 0 examples.

#### Related Terms
- Sharing modules

#### Source
- https://www.nextflow.io/docs/stable/module.html

<details>
<summary>Show full details</summary>

#### Explanation
- Modules are designed to be easy to share and re-use across different pipelines, which helps eliminate duplicate work and spread improvements throughout the community.
- While Nextflow does not provide an explicit mechanism for sharing modules, there are several ways to do it:

#### Allowed Elements
- Simply copy the module files into your pipeline repository
- Use Git submodules to fetch modules from other Git repositories without maintaining a separate copy
- Use the nf-core CLI to install and update modules with a standard approach used by the nf-core community

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## Files

### <a id="files-copying-files"></a>Copying files

**At a glance:** Reference for Copying files.

**Summary:** 0 explanations, 2 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Copying files

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

#### Constraints
- In general, you should not need to manually copy files, because Nextflow will automatically stage files in and out of the task environment based on the definition of process inputs and outputs.
- Ideally, any operation which transforms files should be encapsulated in a process, in order to leverage Nextflowas staging capabilities as much as possible.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-filesystem-operations"></a>Filesystem operations

**At a glance:** Methods for performing filesystem operations such as copying, deleting, and directory listing are documented in the Path reference.

**Summary:** 1 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Filesystem operations

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

#### Explanation
- Methods for performing filesystem operations such as copying, deleting, and directory listing are documented in the Path reference.

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-listing-directories"></a>Listing directories

**At a glance:** Reference for Listing directories.

**Summary:** 2 explanations, 1 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Listing directories

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

#### Explanation
- The simplest way to list a directory is to use list() or listFiles() , which return a collection of first-level elements (files and directories) of a directory:
- As with other each*() methods, eachFile() takes a closure as a parameter:

#### Constraints
- Additionally, the eachFile() method allows you to iterate through the first-level elements only (just like listFiles() ).

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-opening-files"></a>Opening files

**At a glance:** Reference for Opening files.

**Summary:** 6 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Opening files

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

#### Explanation
- To access and work with files, use the file() method, which returns a file system object given a file path string:
- The file() method can reference both files and directories, depending on what the string path refers to in the file system.
- When using the wildcard characters * , ?
- , [] and {} , the argument is interpreted as a glob path matcher and the file() method returns a list object holding the paths of files whose names match the specified pattern, or an empty list if no match is found:
- By default, wildcard characters do not match directories or hidden files.
- For example, if you want to include hidden files in the result list, enable the hidden option:

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-reading-and-writing"></a>Reading and writing

**At a glance:** Reference for Reading and writing.

**Summary:** 0 explanations, 0 constraints, 0 allowed elements, 0 examples.

#### Related Terms
- Reading and writing

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-remote-files"></a>Remote files

**At a glance:** Nextflow works with many types of remote files and objects using the same interface as for local files.

**Summary:** 4 explanations, 0 constraints, 4 allowed elements, 0 examples.

#### Related Terms
- Remote files

#### Source
- https://www.nextflow.io/docs/stable/working-with-files.html

<details>
<summary>Show full details</summary>

#### Explanation
- Nextflow works with many types of remote files and objects using the same interface as for local files.
- The following protocols are supported:
- To reference a remote file, simply specify the URL when opening the file:
- It can then be used in the same way as a local file:

#### Allowed Elements
- HTTP(S)/FTP ( http:// , https:// , ftp:// )
- Amazon S3 ( s3:// )
- Azure Blob Storage ( az:// )
- Google Cloud Storage ( gs:// )

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

