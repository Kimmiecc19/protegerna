# Nextflow Syntax (Mapped, Combined Sources)

![Nextflow Syntax Reference
Banner](https://dummyimage.com/1400x220/0b3d91/ffffff&text=Nextflow+Syntax+Reference)

A grouped reference of Nextflow terms extracted from multiple docs pages,
rendered with quick-glance visual navigation.

## Snapshot

![Total
Terms](https://img.shields.io/badge/Total%20Grouped%20Terms-247-111827?style=for-the-badge)
![Mode](https://img.shields.io/badge/Mode-full-334155?style=for-the-badge)

![Workflow](https://img.shields.io/badge/Workflow-13%20terms-0ea5e9?style=flat-square)
![Process](https://img.shields.io/badge/Process-49%20terms-22c55e?style=flat-square)
![Channel](https://img.shields.io/badge/Channel-12%20terms-06b6d4?style=flat-square)

![Operator](https://img.shields.io/badge/Operator-48%20terms-f59e0b?style=flat-square)
![CLI](https://img.shields.io/badge/CLI-23%20terms-6366f1?style=flat-square)
![Config](https://img.shields.io/badge/Config-29%20terms-ef4444?style=flat-square)

![Types](https://img.shields.io/badge/Types-16%20terms-8b5cf6?style=flat-square)
![Script](https://img.shields.io/badge/Script-48%20terms-14b8a6?style=flat-square)
![Modules](https://img.shields.io/badge/Modules-2%20terms-eab308?style=flat-square)

![Files](https://img.shields.io/badge/Files-7%20terms-64748b?style=flat-square)

> [!TIP]
> Start with the term index table for fast lookup, then expand details only when
> needed.

> [!IMPORTANT]
> Constraints are extracted from multiple documentation pages and may vary by
> Nextflow version.

> **Category Index**
> Each category is grouped into its own block below.
> Use the jump links to move directly to a section.

## Category Index

<details>
<summary>Show details</summary>

<table>
  <tr><td>
<strong>[WF] Workflow</strong><br/>
<a href="#workflow">Jump to section</a><br/>
<em>Terms:</em> 13<br/>
<em>Preview:</em> Workflow, Params, Output, And &amp;amp;, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[PR] Process</strong><br/>
<a href="#process">Jump to section</a><br/>
<em>Terms:</em> 49<br/>
<em>Preview:</em> Modules, accelerator, afterScript, arch, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[CH] Channel</strong><br/>
<a href="#channel">Jump to section</a><br/>
<em>Terms:</em> 12<br/>
<em>Preview:</em> empty, from, fromFilePairs, fromLineage, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[OP] Operator</strong><br/>
<a href="#operator">Jump to section</a><br/>
<em>Terms:</em> 48<br/>
<em>Preview:</em> branch, buffer, collate, collect, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[CLI] CLI</strong><br/>
<a href="#cli">Jump to section</a><br/>
<em>Terms:</em> 23<br/>
<em>Preview:</em> Config, auth, clean, clone, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[CFG] Config</strong><br/>
<a href="#config">Jump to section</a><br/>
<em>Terms:</em> 29<br/>
<em>Preview:</em> apptainer, aws, azure, charliecloud, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[TY] Types</strong><br/>
<a href="#types">Jump to section</a><br/>
<em>Terms:</em> 16<br/>
<em>Preview:</em> Channel, Bag, Boolean, Duration, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[SC] Script</strong><br/>
<a href="#script-language">Jump to section</a><br/>
<em>Terms:</em> 48<br/>
<em>Preview:</em> Process, Function, Enum, Variable, ...
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[MD] Modules</strong><br/>
<a href="#modules">Jump to section</a><br/>
<em>Terms:</em> 2<br/>
<em>Preview:</em> Multiple inclusions, Sharing modules
  </td></tr>
</table>

<table>
  <tr><td>
<strong>[FL] Files</strong><br/>
<a href="#files">Jump to section</a><br/>
<em>Terms:</em> 7<br/>
<em>Preview:</em> Files, Copying files, Filesystem operations, Listing directories, ...
  </td></tr>
</table>

</details>

## Term Index

<details>
<summary>Show details</summary>

Use this table for quick lookup.

<table>
  <thead>
    <tr><th>Term</th><th>Category</th><th>Synopsis</th><th>Related Terms</th></tr>
  </thead>
  <tbody>
    <tr><td><a href="#process-accelerator">accelerator</a></td><td>[PR] Process</td><td>The accelerator directive allows you to request hardware accelerators (e.g.</td><td>accelerator</td></tr>
    <tr><td><a href="#process-afterscript">afterScript</a></td><td>[PR] Process</td><td>The afterScript directive allows you to execute a custom (Bash) snippet immediately after the mai...</td><td>afterScript</td></tr>
    <tr><td><a href="#workflow-and-">And &amp;</a></td><td>[WF] Workflow</td><td>Reference for And &amp;.</td><td>And &amp;amp;</td></tr>
    <tr><td><a href="#config-apptainer">apptainer</a></td><td>[CFG] Config</td><td>The apptainer scope controls how Apptainer containers are executed by Nextflow.</td><td>apptainer</td></tr>
    <tr><td><a href="#process-arch">arch</a></td><td>[PR] Process</td><td>The arch directive allows you to define the CPU architecture to build the software in use by the ...</td><td>arch</td></tr>
    <tr><td><a href="#process-array">array</a></td><td>[PR] Process</td><td>The array directive allows you to submit tasks as job arrays for executors that support it.</td><td>array</td></tr>
    <tr><td><a href="#script-language-assert">assert</a></td><td>[SC] Script Language</td><td>Reference for assert.</td><td>assert</td></tr>
    <tr><td><a href="#script-language-assignment">Assignment</a></td><td>[SC] Script Language</td><td>Reference for Assignment.</td><td>Assignment</td></tr>
    <tr><td><a href="#cli-auth">auth</a></td><td>[CLI] CLI</td><td>Manage Seqera Platform authentication.</td><td>auth</td></tr>
    <tr><td><a href="#config-aws">aws</a></td><td>[CFG] Config</td><td>The aws scope controls the interactions with AWS, including AWS Batch and S3.</td><td>aws</td></tr>
    <tr><td><a href="#config-azure">azure</a></td><td>[CFG] Config</td><td>The azure scope allows you to configure the interactions with Azure, including Azure Batch and Az...</td><td>azure</td></tr>
    <tr><td><a href="#types-bag">Bag</a></td><td>[TY] Types</td><td>Implements the Iterable trait.</td><td>Bag</td></tr>
    <tr><td><a href="#process-beforescript">beforeScript</a></td><td>[PR] Process</td><td>The beforeScript directive allows you to execute a custom (Bash) snippet before the main process ...</td><td>beforeScript</td></tr>
    <tr><td><a href="#script-language-binary-expressions">Binary expressions</a></td><td>[SC] Script Language</td><td>Reference for Binary expressions.</td><td>Binary expressions</td></tr>
    <tr><td><a href="#types-boolean">Boolean</a></td><td>[TY] Types</td><td>Reference for Boolean.</td><td>Boolean</td></tr>
    <tr><td><a href="#operator-branch">branch</a></td><td>[OP] Operator</td><td>Returns: multiple channels</td><td>branch</td></tr>
    <tr><td><a href="#operator-buffer">buffer</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>buffer</td></tr>
    <tr><td><a href="#process-cache">cache</a></td><td>[PR] Process</td><td>The cache directive allows you to store the process results to a local cache.</td><td>cache</td></tr>
    <tr><td><a href="#workflow-calling-processes-and-workflows">Calling processes and workflows</a></td><td>[WF] Workflow</td><td>Reference for Calling processes and workflows.</td><td>Calling processes and workflows</td></tr>
    <tr><td><a href="#script-language-capturing-groups">Capturing groups</a></td><td>[SC] Script Language</td><td>You can match a pattern that includes groups.</td><td>Capturing groups</td></tr>
    <tr><td><a href="#types-channel">Channel</a></td><td>[TY] Types</td><td>A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of val...</td><td>Channel</td></tr>
    <tr><td><a href="#config-charliecloud">charliecloud</a></td><td>[CFG] Config</td><td>The charliecloud scope controls how Charliecloud containers are executed by Nextflow.</td><td>charliecloud</td></tr>
    <tr><td><a href="#cli-clean">clean</a></td><td>[CLI] CLI</td><td>Clean up cache and work directories.</td><td>clean</td></tr>
    <tr><td><a href="#cli-clone">clone</a></td><td>[CLI] CLI</td><td>Clone a remote project into a folder.</td><td>clone</td></tr>
    <tr><td><a href="#script-language-closure">Closure</a></td><td>[SC] Script Language</td><td>Reference for Closure.</td><td>Closure</td></tr>
    <tr><td><a href="#script-language-closures">Closures</a></td><td>[SC] Script Language</td><td>A closure is a function that can be used like a regular value.</td><td>Closures</td></tr>
    <tr><td><a href="#process-clusteroptions">clusterOptions</a></td><td>[PR] Process</td><td>The clusterOptions directive allows the usage of any native configuration option accepted by your...</td><td>clusterOptions</td></tr>
    <tr><td><a href="#operator-collate">collate</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>collate</td></tr>
    <tr><td><a href="#operator-collect">collect</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>collect</td></tr>
    <tr><td><a href="#operator-collectfile">collectFile</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>collectFile</td></tr>
    <tr><td><a href="#operator-combine">combine</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>combine</td></tr>
    <tr><td><a href="#cli-commands">Commands</a></td><td>[CLI] CLI</td><td>Reference for Commands.</td><td>Commands</td></tr>
    <tr><td><a href="#script-language-comments">Comments</a></td><td>[SC] Script Language</td><td>A line comment starts with // and includes the rest of the line.</td><td>Comments</td></tr>
    <tr><td><a href="#operator-concat">concat</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>concat</td></tr>
    <tr><td><a href="#process-conda">conda</a></td><td>[PR] Process</td><td>The conda directive allows for the definition of the process dependencies using the Conda package...</td><td>conda</td></tr>
    <tr><td><a href="#script-language-conditional-execution">Conditional execution</a></td><td>[SC] Script Language</td><td>One of the most important features of any programming language is the ability to execute differen...</td><td>Conditional execution</td></tr>
    <tr><td><a href="#cli-config">Config</a></td><td>[CLI] CLI</td><td>Print the resolved pipeline configuration.</td><td>config, Executor-specific configuration</td></tr>
    <tr><td><a href="#cli-console">console</a></td><td>[CLI] CLI</td><td>Launch the Nextflow interactive console.</td><td>console</td></tr>
    <tr><td><a href="#script-language-constructor-call">Constructor call</a></td><td>[SC] Script Language</td><td>Reference for Constructor call.</td><td>Constructor call</td></tr>
    <tr><td><a href="#process-container">container</a></td><td>[PR] Process</td><td>The container directive allows you to execute the process script in a Docker container.</td><td>container</td></tr>
    <tr><td><a href="#process-containeroptions">containerOptions</a></td><td>[PR] Process</td><td>The containerOptions directive allows you to specify any container execution option supported by ...</td><td>containerOptions</td></tr>
    <tr><td><a href="#files-copying-files">Copying files</a></td><td>[FL] Files</td><td>Reference for Copying files.</td><td>Copying files</td></tr>
    <tr><td><a href="#operator-count">count</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>count</td></tr>
    <tr><td><a href="#operator-countfasta">countFasta</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>countFasta</td></tr>
    <tr><td><a href="#operator-countfastq">countFastq</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>countFastq</td></tr>
    <tr><td><a href="#operator-countjson">countJson</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>countJson</td></tr>
    <tr><td><a href="#operator-countlines">countLines</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>countLines</td></tr>
    <tr><td><a href="#process-cpus">cpus</a></td><td>[PR] Process</td><td>Reference for cpus.</td><td>cpus</td></tr>
    <tr><td><a href="#operator-cross">cross</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>cross</td></tr>
    <tr><td><a href="#config-dag">dag</a></td><td>[CFG] Config</td><td>The dag scope controls the workflow diagram generated by Nextflow.</td><td>dag</td></tr>
    <tr><td><a href="#process-debug">debug</a></td><td>[PR] Process</td><td>By default the stdout produced by the commands executed in all processes is ignored.</td><td>debug</td></tr>
    <tr><td><a href="#script-language-deprecations">Deprecations</a></td><td>[SC] Script Language</td><td>Reference for Deprecations.</td><td>Deprecations</td></tr>
    <tr><td><a href="#process-directives">Directives</a></td><td>[PR] Process</td><td>Reference for Directives.</td><td>Directives</td></tr>
    <tr><td><a href="#process-disk">disk</a></td><td>[PR] Process</td><td>The disk directive allows you to define how much local disk storage the process is allowed to use.</td><td>disk</td></tr>
    <tr><td><a href="#operator-distinct">distinct</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>distinct</td></tr>
    <tr><td><a href="#config-docker">docker</a></td><td>[CFG] Config</td><td>The docker scope controls how Docker containers are executed by Nextflow.</td><td>docker</td></tr>
    <tr><td><a href="#cli-drop">drop</a></td><td>[CLI] CLI</td><td>Delete the local copy of a project.</td><td>drop</td></tr>
    <tr><td><a href="#operator-dump">dump</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>dump</td></tr>
    <tr><td><a href="#types-duration">Duration</a></td><td>[TY] Types</td><td>A Duration represents a duration of time with millisecond precision.</td><td>Duration</td></tr>
    <tr><td><a href="#script-language-dynamic-string">Dynamic string</a></td><td>[SC] Script Language</td><td>Reference for Dynamic string.</td><td>Dynamic string</td></tr>
    <tr><td><a href="#process-echo">echo</a></td><td>[PR] Process</td><td>Reference for echo.</td><td>echo</td></tr>
    <tr><td><a href="#channel-empty">empty</a></td><td>[CH] Channel</td><td>The channel.empty factory method, by definition, creates a channel that doesn&#x27;t emit any value.</td><td>empty</td></tr>
    <tr><td><a href="#script-language-enum">Enum</a></td><td>[SC] Script Language</td><td>An enum type declaration consists of a name and a body.</td><td>Enum type</td></tr>
    <tr><td><a href="#config-env">env</a></td><td>[CFG] Config</td><td>The env scope allows the definition one or more variables that will be exported into the environm...</td><td>env</td></tr>
    <tr><td><a href="#process-errorstrategy">errorStrategy</a></td><td>[PR] Process</td><td>The errorStrategy directive allows you to define how the process manages an error condition.</td><td>errorStrategy</td></tr>
    <tr><td><a href="#process-executor">executor</a></td><td>[PR] Process</td><td>The executor defines the underlying system where processes are executed.</td><td>executor</td></tr>
    <tr><td><a href="#config-executor-specific-defaults">Executor-specific defaults</a></td><td>[CFG] Config</td><td>Some executor settings have different default values depending on the executor.</td><td>Executor-specific defaults</td></tr>
    <tr><td><a href="#script-language-expression-statement">Expression statement</a></td><td>[SC] Script Language</td><td>Any expression can be a statement.</td><td>Expression statement</td></tr>
    <tr><td><a href="#script-language-expressions">Expressions</a></td><td>[SC] Script Language</td><td>An expression represents a value.</td><td>Expressions</td></tr>
    <tr><td><a href="#process-ext">ext</a></td><td>[PR] Process</td><td>The ext is a special directive used as namespace for user custom process directives.</td><td>ext</td></tr>
    <tr><td><a href="#process-fair">fair</a></td><td>[PR] Process</td><td>The fair directive, when enabled, guarantees that process outputs will be emitted in the order in...</td><td>fair</td></tr>
    <tr><td><a href="#script-language-feature-flag">Feature flag</a></td><td>[SC] Script Language</td><td>A feature flag declaration is an assignment.</td><td>Feature flag</td></tr>
    <tr><td><a href="#files-files">Files</a></td><td>[FL] Files</td><td>Reference for Getting file attributes.</td><td>Getting file attributes, Reading and writing an entire file, Appending to a file, Reading a file line by line, ...</td></tr>
    <tr><td><a href="#files-filesystem-operations">Filesystem operations</a></td><td>[FL] Files</td><td>Methods for performing filesystem operations such as copying, deleting, and directory listing are...</td><td>Filesystem operations</td></tr>
    <tr><td><a href="#operator-filter">filter</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>filter</td></tr>
    <tr><td><a href="#operator-first">first</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>first</td></tr>
    <tr><td><a href="#operator-flatmap">flatMap</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>flatMap</td></tr>
    <tr><td><a href="#operator-flatten">flatten</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>flatten</td></tr>
    <tr><td><a href="#types-float">Float</a></td><td>[TY] Types</td><td>A float is a floating-point number (i.e.</td><td>Float</td></tr>
    <tr><td><a href="#channel-from">from</a></td><td>[CH] Channel</td><td>Reference for from.</td><td>from</td></tr>
    <tr><td><a href="#channel-fromfilepairs">fromFilePairs</a></td><td>[CH] Channel</td><td>The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob patter...</td><td>fromFilePairs</td></tr>
    <tr><td><a href="#channel-fromlineage">fromLineage</a></td><td>[CH] Channel</td><td>Reference for fromLineage.</td><td>fromLineage</td></tr>
    <tr><td><a href="#channel-fromlist">fromList</a></td><td>[CH] Channel</td><td>Reference for fromList.</td><td>fromList</td></tr>
    <tr><td><a href="#channel-frompath">fromPath</a></td><td>[CH] Channel</td><td>You can create a channel emitting one or more file paths by using the channel.fromPath method and...</td><td>fromPath</td></tr>
    <tr><td><a href="#channel-fromsra">fromSRA</a></td><td>[CH] Channel</td><td>The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ...</td><td>fromSRA</td></tr>
    <tr><td><a href="#cli-fs">fs</a></td><td>[CLI] CLI</td><td>Perform basic filesystem operations.</td><td>fs</td></tr>
    <tr><td><a href="#script-language-function">Function</a></td><td>[SC] Script Language</td><td>Reference for Function.</td><td>Function, Function call</td></tr>
    <tr><td><a href="#config-fusion">fusion</a></td><td>[CFG] Config</td><td>The fusion scope provides advanced configuration for the use of the Fusion file system .</td><td>fusion</td></tr>
    <tr><td><a href="#process-generic-options">Generic options</a></td><td>[PR] Process</td><td>Reference for Generic options.</td><td>Generic options</td></tr>
    <tr><td><a href="#config-google">google</a></td><td>[CFG] Config</td><td>The google scope allows you to configure the interactions with Google Cloud, including Google Clo...</td><td>google</td></tr>
    <tr><td><a href="#operator-grouptuple">groupTuple</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>groupTuple</td></tr>
    <tr><td><a href="#script-language-hello-world">Hello world</a></td><td>[SC] Script Language</td><td>Reference for Hello world.</td><td>Hello world</td></tr>
    <tr><td><a href="#cli-help">help</a></td><td>[CLI] CLI</td><td>Print the top-level help or specific help for a command.</td><td>help</td></tr>
    <tr><td><a href="#script-language-ifelse">if/else</a></td><td>[SC] Script Language</td><td>An if/else statement consists of an if branch and an optional else branch .</td><td>if/else</td></tr>
    <tr><td><a href="#operator-ifempty">ifEmpty</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>ifEmpty</td></tr>
    <tr><td><a href="#script-language-include">Include</a></td><td>[SC] Script Language</td><td>Reference for Include.</td><td>Include</td></tr>
    <tr><td><a href="#script-language-index-expression">Index expression</a></td><td>[SC] Script Language</td><td>Reference for Index expression.</td><td>Index expression</td></tr>
    <tr><td><a href="#workflow-index-files">Index files</a></td><td>[WF] Workflow</td><td>Each output can create an index file of the values that were published.</td><td>Index files</td></tr>
    <tr><td><a href="#cli-info">info</a></td><td>[CLI] CLI</td><td>Print project or system runtime information.</td><td>info</td></tr>
    <tr><td><a href="#process-inputs">Inputs</a></td><td>[PR] Process</td><td>Reference for Inputs.</td><td>Inputs</td></tr>
    <tr><td><a href="#process-inputs-and-outputs-legacy">Inputs and outputs (legacy)</a></td><td>[PR] Process</td><td>Reference for Inputs and outputs (legacy).</td><td>Inputs and outputs (legacy)</td></tr>
    <tr><td><a href="#process-inputs-and-outputs-typed">Inputs and outputs (typed)</a></td><td>[PR] Process</td><td>Reference for Inputs and outputs (typed).</td><td>Inputs and outputs (typed)</td></tr>
    <tr><td><a href="#cli-inspect">inspect</a></td><td>[CLI] CLI</td><td>Inspect process settings in a pipeline project.</td><td>inspect</td></tr>
    <tr><td><a href="#types-integer">Integer</a></td><td>[TY] Types</td><td>An integer is a whole number that can be positive or negative.</td><td>Integer</td></tr>
    <tr><td><a href="#channel-interval">interval</a></td><td>[CH] Channel</td><td>The interval method emits an incrementing index (starting from zero) at a periodic interval.</td><td>interval</td></tr>
    <tr><td><a href="#types-iterable">Iterable</a></td><td>[TY] Types</td><td>Implemented by the following types: Bag , List , Set</td><td>Iterable</td></tr>
    <tr><td><a href="#config-java-settings">Java settings</a></td><td>[CFG] Config</td><td>Reference for Java settings.</td><td>Java settings</td></tr>
    <tr><td><a href="#operator-join">join</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>join</td></tr>
    <tr><td><a href="#config-k8s">k8s</a></td><td>[CFG] Config</td><td>The k8s scope controls the deployment and execution of workflow applications in a Kubernetes clus...</td><td>k8s</td></tr>
    <tr><td><a href="#cli-kuberun">kuberun</a></td><td>[CLI] CLI</td><td>Launch a Nextflow pipeline on a Kubernetes cluster.</td><td>kuberun</td></tr>
    <tr><td><a href="#process-label">label</a></td><td>[PR] Process</td><td>The label directive allows the annotation of processes with mnemonic identifier of your choice.</td><td>label</td></tr>
    <tr><td><a href="#operator-last">last</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>last</td></tr>
    <tr><td><a href="#cli-launch">launch</a></td><td>[CLI] CLI</td><td>Launch a workflow in Seqera Platform .</td><td>launch</td></tr>
    <tr><td><a href="#workflow-legacy-parameters">Legacy parameters</a></td><td>[WF] Workflow</td><td>Reference for Legacy parameters.</td><td>Legacy parameters</td></tr>
    <tr><td><a href="#cli-lineage">lineage</a></td><td>[CLI] CLI</td><td>Inspect lineage metadata for Nextflow runs.</td><td>lineage</td></tr>
    <tr><td><a href="#cli-lint">lint</a></td><td>[CLI] CLI</td><td>Lint Nextflow scripts and config files.</td><td>lint</td></tr>
    <tr><td><a href="#script-language-list">List</a></td><td>[SC] Script Language</td><td>Reference for List.</td><td>List</td></tr>
    <tr><td><a href="#cli-list">list</a></td><td>[CLI] CLI</td><td>List all downloaded projects.</td><td>list</td></tr>
    <tr><td><a href="#types-list">List</a></td><td>[TY] Types</td><td>Implements the Iterable trait.</td><td>List</td></tr>
    <tr><td><a href="#files-listing-directories">Listing directories</a></td><td>[FL] Files</td><td>Reference for Listing directories.</td><td>Listing directories</td></tr>
    <tr><td><a href="#script-language-lists">Lists</a></td><td>[SC] Script Language</td><td>Reference for Lists.</td><td>Lists</td></tr>
    <tr><td><a href="#cli-log">log</a></td><td>[CLI] CLI</td><td>Print the execution history and log information.</td><td>log</td></tr>
    <tr><td><a href="#process-machinetype">machineType</a></td><td>[PR] Process</td><td>The machineType can be used to specify a predefined Google Compute Platform machine type when run...</td><td>machineType</td></tr>
    <tr><td><a href="#config-mail">mail</a></td><td>[CFG] Config</td><td>The mail scope controls the mail server used to send email notifications.</td><td>mail</td></tr>
    <tr><td><a href="#config-manifest">manifest</a></td><td>[CFG] Config</td><td>The manifest scope allows you to define some metadata that is useful when publishing or running y...</td><td>manifest</td></tr>
    <tr><td><a href="#script-language-map">Map</a></td><td>[SC] Script Language</td><td>A map literal consists of a comma-separated list of one or more map entries , enclosed in square ...</td><td>Map</td></tr>
    <tr><td><a href="#operator-map">map</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>map</td></tr>
    <tr><td><a href="#types-map">Map</a></td><td>[TY] Types</td><td>A map associates or maps keys of type K to values of type V .</td><td>Map</td></tr>
    <tr><td><a href="#script-language-maps">Maps</a></td><td>[SC] Script Language</td><td>Maps are used to store associative arrays (also known as dictionaries ).</td><td>Maps</td></tr>
    <tr><td><a href="#operator-max">max</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>max</td></tr>
    <tr><td><a href="#process-maxerrors">maxErrors</a></td><td>[PR] Process</td><td>The maxErrors directive allows you to specify the maximum number of times a process can fail when...</td><td>maxErrors</td></tr>
    <tr><td><a href="#process-maxforks">maxForks</a></td><td>[PR] Process</td><td>The maxForks directive allows you to define the maximum number of process instances that can be e...</td><td>maxForks</td></tr>
    <tr><td><a href="#process-maxretries">maxRetries</a></td><td>[PR] Process</td><td>The maxRetries directive allows you to define the maximum number of times a process instance can ...</td><td>maxRetries</td></tr>
    <tr><td><a href="#process-maxsubmitawait">maxSubmitAwait</a></td><td>[PR] Process</td><td>The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue...</td><td>maxSubmitAwait</td></tr>
    <tr><td><a href="#process-memory">memory</a></td><td>[PR] Process</td><td>The memory directive allows you to define how much memory the process is allowed to use.</td><td>memory</td></tr>
    <tr><td><a href="#types-memoryunit">MemoryUnit</a></td><td>[TY] Types</td><td>A MemoryUnit represents a quantity of bytes.</td><td>MemoryUnit</td></tr>
    <tr><td><a href="#operator-merge">merge</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>merge</td></tr>
    <tr><td><a href="#operator-min">min</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>min</td></tr>
    <tr><td><a href="#operator-mix">mix</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>mix</td></tr>
    <tr><td><a href="#process-modules">Modules</a></td><td>[PR] Process</td><td>Environment Modules is a package manager that allows you to dynamically configure your execution ...</td><td>module, Module inclusion, Module directory, Module aliases, ...</td></tr>
    <tr><td><a href="#script-language-multi-line-strings">Multi-line strings</a></td><td>[SC] Script Language</td><td>Reference for Multi-line strings.</td><td>Multi-line strings</td></tr>
    <tr><td><a href="#operator-multimap">multiMap</a></td><td>[OP] Operator</td><td>Returns: multiple channels</td><td>multiMap</td></tr>
    <tr><td><a href="#modules-multiple-inclusions">Multiple inclusions</a></td><td>[MD] Modules</td><td>A Nextflow script can include any number of modules, and an include statement can import any numb...</td><td>Multiple inclusions</td></tr>
    <tr><td><a href="#workflow-named-workflows">Named workflows</a></td><td>[WF] Workflow</td><td>Reference for Named workflows.</td><td>Named workflows</td></tr>
    <tr><td><a href="#config-nextflow">nextflow</a></td><td>[CFG] Config</td><td>Reference for nextflow.</td><td>nextflow</td></tr>
    <tr><td><a href="#config-nextflow-settings">Nextflow settings</a></td><td>[CFG] Config</td><td>Reference for Nextflow settings.</td><td>Nextflow settings</td></tr>
    <tr><td><a href="#config-notification">notification</a></td><td>[CFG] Config</td><td>The notification scope controls the automatic sending of an email notification on workflow comple...</td><td>notification</td></tr>
    <tr><td><a href="#script-language-null">Null</a></td><td>[SC] Script Language</td><td>The null literal is specified as null .</td><td>Null</td></tr>
    <tr><td><a href="#script-language-number">Number</a></td><td>[SC] Script Language</td><td>A number literal can be an integer or floating-point number, and can be positive or negative.</td><td>Number</td></tr>
    <tr><td><a href="#channel-of">of</a></td><td>[CH] Channel</td><td>Reference for of.</td><td>of</td></tr>
    <tr><td><a href="#files-opening-files">Opening files</a></td><td>[FL] Files</td><td>Reference for Opening files.</td><td>Opening files</td></tr>
    <tr><td><a href="#types-operations">Operations</a></td><td>[TY] Types</td><td>A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, an...</td><td>Operations</td></tr>
    <tr><td><a href="#script-language-operators">Operators</a></td><td>[SC] Script Language</td><td>Operators are symbols that perform specific functions on one or more values, and generally make c...</td><td>Operators</td></tr>
    <tr><td><a href="#cli-options">Options</a></td><td>[CLI] CLI</td><td>The top-level options are meant to be invoked in relation to the core Nextflow application and ar...</td><td>Options</td></tr>
    <tr><td><a href="#config-other-settings">Other settings</a></td><td>[CFG] Config</td><td>Reference for Other settings.</td><td>Other settings</td></tr>
    <tr><td><a href="#workflow-output">Output</a></td><td>[WF] Workflow</td><td>The output block consists of one or more output declarations .</td><td>Output block, Output directives</td></tr>
    <tr><td><a href="#process-outputs">Outputs</a></td><td>[PR] Process</td><td>Reference for Outputs.</td><td>Outputs</td></tr>
    <tr><td><a href="#workflow-parameters">Parameters</a></td><td>[WF] Workflow</td><td>Parameters can be declared in a Nextflow script with the params block or with legacy parameter de...</td><td>Parameters</td></tr>
    <tr><td><a href="#workflow-params">Params</a></td><td>[WF] Workflow</td><td>The params block consists of one or more parameter declarations .</td><td>Params block, Parameter (legacy)</td></tr>
    <tr><td><a href="#script-language-parentheses">Parentheses</a></td><td>[SC] Script Language</td><td>Reference for Parentheses.</td><td>Parentheses</td></tr>
    <tr><td><a href="#process-penv">penv</a></td><td>[PR] Process</td><td>The penv directive allows you to define the parallel environment to be used when submitting a par...</td><td>penv</td></tr>
    <tr><td><a href="#workflow-pipe-">Pipe |</a></td><td>[WF] Workflow</td><td>Reference for Pipe |.</td><td>Pipe |</td></tr>
    <tr><td><a href="#cli-plugin">plugin</a></td><td>[CLI] CLI</td><td>Manage plugins and run plugin-specific commands.</td><td>plugin</td></tr>
    <tr><td><a href="#process-pod">pod</a></td><td>[PR] Process</td><td>The pod directive allows the definition of pod specific settings, such as environment variables, ...</td><td>pod</td></tr>
    <tr><td><a href="#config-podman">podman</a></td><td>[CFG] Config</td><td>The podman scope controls how Podman containers are executed by Nextflow.</td><td>podman</td></tr>
    <tr><td><a href="#script-language-precedence">Precedence</a></td><td>[SC] Script Language</td><td>Reference for Precedence.</td><td>Precedence</td></tr>
    <tr><td><a href="#script-language-process">Process</a></td><td>[SC] Script Language</td><td>A process consists of a name and a body.</td><td>Process, Process (typed)</td></tr>
    <tr><td><a href="#script-language-property-expression">Property expression</a></td><td>[SC] Script Language</td><td>Reference for Property expression.</td><td>Property expression</td></tr>
    <tr><td><a href="#process-publishdir">publishDir</a></td><td>[PR] Process</td><td>The publishDir directive allows you to publish the process output files to a specified folder.</td><td>publishDir</td></tr>
    <tr><td><a href="#workflow-publishing-files">Publishing files</a></td><td>[WF] Workflow</td><td>Reference for Publishing files.</td><td>Publishing files</td></tr>
    <tr><td><a href="#cli-pull">pull</a></td><td>[CLI] CLI</td><td>Download or update a project.</td><td>pull</td></tr>
    <tr><td><a href="#process-queue">queue</a></td><td>[PR] Process</td><td>The queue directive allows you to set the queue where jobs are scheduled when using a grid based ...</td><td>queue</td></tr>
    <tr><td><a href="#operator-randomsample">randomSample</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>randomSample</td></tr>
    <tr><td><a href="#files-reading-and-writing">Reading and writing</a></td><td>[FL] Files</td><td>Reference for Reading and writing.</td><td>Reading and writing</td></tr>
    <tr><td><a href="#operator-reduce">reduce</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>reduce</td></tr>
    <tr><td><a href="#script-language-regular-expressions">Regular expressions</a></td><td>[SC] Script Language</td><td>Regular expressions are the Swiss Army knife of text processing.</td><td>Regular expressions</td></tr>
    <tr><td><a href="#files-remote-files">Remote files</a></td><td>[FL] Files</td><td>Nextflow works with many types of remote files and objects using the same interface as for local ...</td><td>Remote files</td></tr>
    <tr><td><a href="#config-report">report</a></td><td>[CFG] Config</td><td>The report scope allows you to configure the workflow Execution report .</td><td>report</td></tr>
    <tr><td><a href="#process-resourcelabels">resourceLabels</a></td><td>[PR] Process</td><td>The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies ...</td><td>resourceLabels</td></tr>
    <tr><td><a href="#process-resourcelimits">resourceLimits</a></td><td>[PR] Process</td><td>The resourceLimits directive allows you to specify environment-specific limits for task resource ...</td><td>resourceLimits</td></tr>
    <tr><td><a href="#script-language-return">return</a></td><td>[SC] Script Language</td><td>Reference for return.</td><td>return</td></tr>
    <tr><td><a href="#cli-run">run</a></td><td>[CLI] CLI</td><td>Execute a pipeline.</td><td>run</td></tr>
    <tr><td><a href="#config-sarus">sarus</a></td><td>[CFG] Config</td><td>The sarus scope controls how Sarus containers are executed by Nextflow.</td><td>sarus</td></tr>
    <tr><td><a href="#process-scratch">scratch</a></td><td>[PR] Process</td><td>The scratch directive allows you to execute the process in a temporary folder that is local to th...</td><td>scratch</td></tr>
    <tr><td><a href="#script-language-script-declarations">Script declarations</a></td><td>[SC] Script Language</td><td>Reference for Script declarations.</td><td>Script declarations</td></tr>
    <tr><td><a href="#script-language-script-definitions">Script definitions</a></td><td>[SC] Script Language</td><td>So far, we have been focusing on the basic building blocks of Nextflow code, like variables, list...</td><td>Script definitions</td></tr>
    <tr><td><a href="#process-secret">secret</a></td><td>[PR] Process</td><td>The secret directive allows a process to access secrets.</td><td>secret</td></tr>
    <tr><td><a href="#cli-secrets">secrets</a></td><td>[CLI] CLI</td><td>Manage pipeline secrets .</td><td>secrets</td></tr>
    <tr><td><a href="#cli-self-update">self-update</a></td><td>[CLI] CLI</td><td>Update the nextflow runtime to the latest available version.</td><td>self-update</td></tr>
    <tr><td><a href="#config-seqera-platform-settings">Seqera Platform settings</a></td><td>[CFG] Config</td><td>Reference for Seqera Platform settings.</td><td>Seqera Platform settings</td></tr>
    <tr><td><a href="#operator-set">set</a></td><td>[OP] Operator</td><td>Returns: nothing</td><td>set</td></tr>
    <tr><td><a href="#types-set">Set</a></td><td>[TY] Types</td><td>Implements the Iterable trait.</td><td>Set</td></tr>
    <tr><td><a href="#modules-sharing-modules">Sharing modules</a></td><td>[MD] Modules</td><td>Modules are designed to be easy to share and re-use across different pipelines, which helps elimi...</td><td>Sharing modules</td></tr>
    <tr><td><a href="#script-language-shebang">Shebang</a></td><td>[SC] Script Language</td><td>Reference for Shebang.</td><td>Shebang</td></tr>
    <tr><td><a href="#process-shell">shell</a></td><td>[PR] Process</td><td>The shell directive allows you to define a custom shell command for process scripts.</td><td>shell</td></tr>
    <tr><td><a href="#config-shifter">shifter</a></td><td>[CFG] Config</td><td>The shifter scope controls how Shifter containers are executed by Nextflow.</td><td>shifter</td></tr>
    <tr><td><a href="#config-singularity">singularity</a></td><td>[CFG] Config</td><td>The singularity scope controls how Singularity containers are executed by Nextflow.</td><td>singularity</td></tr>
    <tr><td><a href="#process-spack">spack</a></td><td>[PR] Process</td><td>The spack directive allows for the definition of the process dependencies using the Spack package...</td><td>spack</td></tr>
    <tr><td><a href="#workflow-special-operators">Special operators</a></td><td>[WF] Workflow</td><td>The following operators have a special meaning when used in a workflow with process and workflow ...</td><td>Special operators</td></tr>
    <tr><td><a href="#operator-splitcsv">splitCsv</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>splitCsv</td></tr>
    <tr><td><a href="#operator-splitfasta">splitFasta</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>splitFasta</td></tr>
    <tr><td><a href="#operator-splitfastq">splitFastq</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>splitFastq</td></tr>
    <tr><td><a href="#operator-splitjson">splitJson</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>splitJson</td></tr>
    <tr><td><a href="#operator-splittext">splitText</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>splitText</td></tr>
    <tr><td><a href="#process-stage-directives">Stage directives</a></td><td>[PR] Process</td><td>Reference for Stage directives.</td><td>Stage directives</td></tr>
    <tr><td><a href="#process-stageinmode">stageInMode</a></td><td>[PR] Process</td><td>The stageInMode directive defines how input files are staged into the process work directory.</td><td>stageInMode</td></tr>
    <tr><td><a href="#process-stageoutmode">stageOutMode</a></td><td>[PR] Process</td><td>The stageOutMode directive defines how output files are staged out from the scratch directory to ...</td><td>stageOutMode</td></tr>
    <tr><td><a href="#script-language-statements">Statements</a></td><td>[SC] Script Language</td><td>Reference for Statements.</td><td>Statements</td></tr>
    <tr><td><a href="#process-storedir">storeDir</a></td><td>[PR] Process</td><td>The storeDir directive allows you to define a directory that is used as a permanent cache for you...</td><td>storeDir</td></tr>
    <tr><td><a href="#types-string">String</a></td><td>[TY] Types</td><td>Reference for String.</td><td>String</td></tr>
    <tr><td><a href="#script-language-string-interpolation">String interpolation</a></td><td>[SC] Script Language</td><td>There is an important difference between single-quoted and double-quoted strings: Double-quoted s...</td><td>String interpolation</td></tr>
    <tr><td><a href="#script-language-string-replacement">String replacement</a></td><td>[SC] Script Language</td><td>Reference for String replacement.</td><td>String replacement</td></tr>
    <tr><td><a href="#script-language-strings">Strings</a></td><td>[SC] Script Language</td><td>Reference for Strings.</td><td>Strings</td></tr>
    <tr><td><a href="#operator-subscribe">subscribe</a></td><td>[OP] Operator</td><td>Returns: nothing</td><td>subscribe</td></tr>
    <tr><td><a href="#operator-sum">sum</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>sum</td></tr>
    <tr><td><a href="#process-tag">tag</a></td><td>[PR] Process</td><td>The tag directive allows you to associate each process execution with a custom label, so that it ...</td><td>tag</td></tr>
    <tr><td><a href="#operator-take">take</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>take</td></tr>
    <tr><td><a href="#workflow-takes-and-emits">Takes and emits</a></td><td>[WF] Workflow</td><td>Reference for Takes and emits.</td><td>Takes and emits</td></tr>
    <tr><td><a href="#operator-tap">tap</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>tap</td></tr>
    <tr><td><a href="#process-task-properties">Task properties</a></td><td>[PR] Process</td><td>Reference for Task properties.</td><td>Task properties</td></tr>
    <tr><td><a href="#script-language-ternary-expression">Ternary expression</a></td><td>[SC] Script Language</td><td>Reference for Ternary expression.</td><td>Ternary expression</td></tr>
    <tr><td><a href="#script-language-throw">throw</a></td><td>[SC] Script Language</td><td>Reference for throw.</td><td>throw</td></tr>
    <tr><td><a href="#process-time">time</a></td><td>[PR] Process</td><td>The time directive allows you to define how long a process is allowed to run.</td><td>time</td></tr>
    <tr><td><a href="#config-timeline">timeline</a></td><td>[CFG] Config</td><td>The timeline scope controls the execution timeline report generated by Nextflow.</td><td>timeline</td></tr>
    <tr><td><a href="#operator-tointeger">toInteger</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>toInteger</td></tr>
    <tr><td><a href="#operator-tolist">toList</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>toList</td></tr>
    <tr><td><a href="#channel-topic">topic</a></td><td>[CH] Channel</td><td>A topic channel is a channel that can receive values from many sources implicitly based on a matc...</td><td>topic</td></tr>
    <tr><td><a href="#operator-tosortedlist">toSortedList</a></td><td>[OP] Operator</td><td>Returns: dataflow value</td><td>toSortedList</td></tr>
    <tr><td><a href="#config-tower">tower</a></td><td>[CFG] Config</td><td>The tower scope controls the settings for Seqera Platform (formerly Tower Cloud).</td><td>tower</td></tr>
    <tr><td><a href="#config-trace">trace</a></td><td>[CFG] Config</td><td>The trace scope controls the layout of the execution trace file generated by Nextflow.</td><td>trace</td></tr>
    <tr><td><a href="#operator-transpose">transpose</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>transpose</td></tr>
    <tr><td><a href="#script-language-trycatch">try/catch</a></td><td>[SC] Script Language</td><td>Reference for try/catch.</td><td>try/catch</td></tr>
    <tr><td><a href="#types-tuple">Tuple</a></td><td>[TY] Types</td><td>A tuple is a fixed sequence of values, where each value can have its own type.</td><td>Tuple</td></tr>
    <tr><td><a href="#script-language-tuples">Tuples</a></td><td>[SC] Script Language</td><td>Tuples are used to store a fixed sequence of heterogeneous values.</td><td>Tuples</td></tr>
    <tr><td><a href="#script-language-unary-expressions">Unary expressions</a></td><td>[SC] Script Language</td><td>Reference for Unary expressions.</td><td>Unary expressions</td></tr>
    <tr><td><a href="#operator-unique">unique</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>unique</td></tr>
    <tr><td><a href="#config-unscoped-options">Unscoped options</a></td><td>[CFG] Config</td><td>Reference for Unscoped options.</td><td>Unscoped options</td></tr>
    <tr><td><a href="#operator-until">until</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>until</td></tr>
    <tr><td><a href="#channel-value">value</a></td><td>[CH] Channel</td><td>The channel.value function creates a dataflow value bound to the given argument.</td><td>value</td></tr>
    <tr><td><a href="#types-value">Value</a></td><td>[TY] Types</td><td>A dataflow value (also known as a value channel ) is an asynchronous value of type V .</td><td>Value</td></tr>
    <tr><td><a href="#script-language-variable">Variable</a></td><td>[SC] Script Language</td><td>Reference for Variable declaration.</td><td>Variable declaration, Variable</td></tr>
    <tr><td><a href="#script-language-variables">Variables</a></td><td>[SC] Script Language</td><td>Reference for Variables.</td><td>Variables</td></tr>
    <tr><td><a href="#types-versionnumber">VersionNumber</a></td><td>[TY] Types</td><td>A VersionNumber represents a semantic or calendar version number.</td><td>VersionNumber</td></tr>
    <tr><td><a href="#operator-view">view</a></td><td>[OP] Operator</td><td>Returns: channel</td><td>view</td></tr>
    <tr><td><a href="#channel-watchpath">watchPath</a></td><td>[CH] Channel</td><td>The channel.watchPath method watches a folder for one or more files matching a specified pattern.</td><td>watchPath</td></tr>
    <tr><td><a href="#config-wave">wave</a></td><td>[CFG] Config</td><td>The wave scope provides advanced configuration for the use of Wave containers .</td><td>wave</td></tr>
    <tr><td><a href="#workflow-workflow">Workflow</a></td><td>[WF] Workflow</td><td>A workflow can be a named workflow or an entry workflow .</td><td>Workflow, workflow, Entry workflow, Process and workflow recursion, ...</td></tr>
  </tbody>
</table>

</details>

## Sources

<details>
<summary>Show details</summary>

<table>
  <thead>
    <tr><th>Source URL</th></tr>
  </thead>
  <tbody>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/syntax.html" target="_blank">https://www.nextflow.io/docs/stable/reference/syntax.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/config.html" target="_blank">https://www.nextflow.io/docs/stable/reference/config.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/workflow.html" target="_blank">https://www.nextflow.io/docs/stable/workflow.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/stdlib-types.html" target="_blank">https://www.nextflow.io/docs/stable/reference/stdlib-types.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/cli.html" target="_blank">https://www.nextflow.io/docs/stable/reference/cli.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/process.html" target="_blank">https://www.nextflow.io/docs/stable/reference/process.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/module.html" target="_blank">https://www.nextflow.io/docs/stable/module.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/working-with-files.html" target="_blank">https://www.nextflow.io/docs/stable/working-with-files.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/operator.html" target="_blank">https://www.nextflow.io/docs/stable/reference/operator.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/script.html" target="_blank">https://www.nextflow.io/docs/stable/script.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/channel.html" target="_blank">https://www.nextflow.io/docs/stable/reference/channel.html</a></td></tr>
    <tr><td><a href="https://www.nextflow.io/docs/stable/reference/env-vars.html" target="_blank">https://www.nextflow.io/docs/stable/reference/env-vars.html</a></td></tr>
  </tbody>
</table>

</details>

## [WF] Workflow

### <a id="workflow-workflow"></a>[WF] Workflow

<table>
  <tr><td>
<strong>[WF] Workflow</strong><br/>
A workflow can be a named workflow or an entry workflow .<br/>
  </td></tr>
</table>

**At a glance:** A workflow can be a named workflow or an entry workflow .

#### Related Terms
- Workflow
- workflow
- Entry workflow
- Process and workflow recursion
- Workflow outputs

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A workflow can be a named workflow or an entry workflow .</li>
  <li>A named workflow consists of a name and a body, and may consist of a take , main , and emit section:</li>
  <li>An entry workflow has no name and may consist of a main , publish , onComplete , and onError section:</li>
  <li>Entry workflow definitions are ignored when a script is included as a module.</li>
  <li>This way, the same script can be included as a module or executed as a pipeline.</li>
  <li>The workflow scope provides workflow execution options.</li>
  <li>The following settings are available:</li>
  <li>A script can define up to one entry workflow , which does not have a name and serves as the entrypoint of the script:</li>
  <li>Processes can be invoked recursively using the recurse method.</li>
  <li>In the above example, the count_down process is first invoked with the value params.start .</li>
  <li>On each subsequent iteration, the process is invoked again using the output from the previous iteration.</li>
  <li>The recursion continues until the specified condition is satisfied, as defined by the until method, which terminates the recursion.</li>
  <li>The recursive output can also be limited using the times method:</li>
  <li>Workflows can also be invoked recursively:</li>
  <li>Limitations</li>
  <li>A script can define an output block which declares the top-level outputs of the workflow.</li>
  <li>Any channel in the workflow can be assigned to an output, including process and subworkflow outputs.</li>
  <li>This approach is intended to replace the publishDir directive.</li>
  <li>Here is a basic example:</li>
  <li>In the above example, the output of process fetch is assigned to the samples workflow output.</li>
  <li>How this output is published to a directory structure is described in the next section.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>In order for a script to be executable, it must either define an entry workflow or be a code snippet as described above .</li>
  <li>Each output should be assigned in the publish section of the entry workflow.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>The take, emit, and publish sections are optional. The main: section label can be omitted if they are not specified.</li>
  <li>The take section consists of one or more parameters.</li>
  <li>The main section consists of one or more statements .</li>
  <li>The emit section consists of one or more emit statements . An emit statement can be a variable name , an assignment , or an expression statement . If an emit statement is an expression statement, it must be the only emit.</li>
  <li>Only one entry workflow may be defined in a script.</li>
  <li>The main: section label can be omitted if the other sections are not specified.</li>
  <li>The publish section consists of one or more publish statements . A publish statement is an assignment , where the assignment target is the name of a workflow output.</li>
  <li>The onComplete and onError sections consist of one or more statements .</li>
  <li>A recursive process or workflow must have matching inputs and outputs, such that the outputs for each iteration can be supplied as the inputs for the next iteration.</li>
  <li>Recursive workflows cannot use reduction operators such as collect , reduce , and toList , because these operators cause the recursion to hang indefinitely after the initial iteration.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-params"></a>[WF] Params

<table>
  <tr><td>
<strong>[WF] Params</strong><br/>
The params block consists of one or more parameter declarations .<br/>
  </td></tr>
</table>

**At a glance:** The params block consists of one or more parameter declarations
.

#### Related Terms
- Params block
- Parameter (legacy)

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The params block consists of one or more parameter declarations .</li>
  <li>A parameter declaration consists of a name, type, and an optional default value:</li>
  <li>A legacy parameter declaration is an assignment.</li>
  <li>Parameters supplied via command line options, params files, and config files take precedence over parameter definitions in a script.</li>
  <li>A script can declare parameters using the params block:</li>
  <li>The following types can be used for parameters:</li>
  <li>Parameters can be used in the entry workflow:</li>
  <li>The default value can be overridden by the command line, params file, or config file.</li>
  <li>Parameters from multiple sources are resolved in the order described in Pipeline parameters .</li>
  <li>Parameters specified on the command line are converted to the appropriate type based on the corresponding type annotation.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Only one params block may be defined in a script.</li>
  <li>The target should be a pipeline parameter and the source should be an expression:</li>
  <li>A parameter that doesn&#x27;t specify a default value is a required param.</li>
  <li>If a required param is not given a value at runtime, the run will fail.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Boolean</li>
  <li>Float</li>
  <li>Integer</li>
  <li>Path</li>
  <li>String</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-output"></a>[WF] Output

<table>
  <tr><td>
<strong>[WF] Output</strong><br/>
The output block consists of one or more output declarations .<br/>
  </td></tr>
</table>

**At a glance:** The output block consists of one or more output declarations .

#### Related Terms
- Output block
- Output directives

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The output block consists of one or more output declarations .</li>
  <li>Each output declaration consists of a name and one or more output directives for defining the output:</li>
  <li>See Workflow outputs for the set of available output directives.</li>
  <li>The following directives are available for each output in the output block:</li>
  <li>Additionally, the following options from the workflow config scope can be specified as directives:</li>
  <li>For example:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Only one output block may be defined in a script.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>contentType</li>
  <li>enabled</li>
  <li>ignoreErrors</li>
  <li>mode</li>
  <li>overwrite</li>
  <li>storageClass</li>
  <li>tags</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-and-"></a>[WF] And &amp;

<table>
  <tr><td>
<strong>[WF] And &amp;</strong><br/>
Reference for And &amp;.<br/>
  </td></tr>
</table>

**At a glance:** Reference for And &.

#### Related Terms
- And &amp;

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The &amp; and operator can be used to call multiple processes in parallel with the same channel(s):</li>
  <li>In the above snippet, the initial channel is piped to the map operator, which reverses the string value.</li>
  <li>Then, the result is passed to the processes greet and to_upper , which are executed in parallel.</li>
  <li>Each process outputs a channel, and the two channels are combined using the mix operator.</li>
  <li>Finally, the result is printed using the view operator.</li>
  <li>The same code can also be written as:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-calling-processes-and-workflows"></a>[WF] Calling processes and workflows

<table>
  <tr><td>
<strong>[WF] Calling processes and workflows</strong><br/>
Reference for Calling processes and workflows.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Calling processes and workflows.

#### Related Terms
- Calling processes and workflows

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Processes and workflows are called like functions, passing their inputs as arguments:</li>
  <li>Processes and workflows have a few extra rules for how they can be called:</li>
  <li>The areturn valuea of a process or workflow call is the process outputs or workflow emits, respectively.</li>
  <li>The return value can be assigned to a variable or passed into another call:</li>
  <li>Named outputs can be accessed as properties of the return value:</li>
  <li>As a convenience, process and workflow outputs can also be accessed without first assigning to a variable, by using the .out property of the process or workflow name:</li>
  <li>Workflows can be composed in the same way:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Processes and workflows can only be called by workflows</li>
  <li>A given process or workflow can only be called once in a given workflow. To use a process or workflow multiple times in the same workflow, use Module aliases .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-index-files"></a>[WF] Index files

<table>
  <tr><td>
<strong>[WF] Index files</strong><br/>
Each output can create an index file of the values that were published.<br/>
  </td></tr>
</table>

**At a glance:** Each output can create an index file of the values that were
published.

#### Related Terms
- Index files

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Each output can create an index file of the values that were published.</li>
  <li>An index file preserves the structure of channel values, including metadata, which is simpler than encoding this information with directories and file names.</li>
  <li>The index file can be a CSV ( .csv ), JSON ( .json ), or YAML ( .yml , .yaml ) file.</li>
  <li>For example:</li>
  <li>The above example will write the following CSV file to results/samples.csv :</li>
  <li>You can customize the index file with additional directives, for example:</li>
  <li>This example will produce the following index file:</li>
  <li>See Output directives for the list of available index directives.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The channel values should be files, lists, or maps.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-legacy-parameters"></a>[WF] Legacy parameters

<table>
  <tr><td>
<strong>[WF] Legacy parameters</strong><br/>
Reference for Legacy parameters.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Legacy parameters.

#### Related Terms
- Legacy parameters

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Parameters can be declared by assigning a params property to a default value:</li>
  <li>The default value can be overridden by the command line, params file, or config file.</li>
  <li>Parameters from multiple sources are resolved in the order described in Pipeline parameters .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-named-workflows"></a>[WF] Named workflows

<table>
  <tr><td>
<strong>[WF] Named workflows</strong><br/>
Reference for Named workflows.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Named workflows.

#### Related Terms
- Named workflows

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A named workflow is a workflow that can be called by other workflows:</li>
  <li>The above example defines a workflow named my_workflow which is called by the entry workflow.</li>
  <li>Both hello and bye could be any other process or workflow.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-parameters"></a>[WF] Parameters

<table>
  <tr><td>
<strong>[WF] Parameters</strong><br/>
Parameters can be declared in a Nextflow script with the params block or with
legacy parameter declarations.<br/>
  </td></tr>
</table>

**At a glance:** Parameters can be declared in a Nextflow script with the params
block or with legacy parameter declarations.

#### Related Terms
- Parameters

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Parameters can be declared in a Nextflow script with the params block or with legacy parameter declarations.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-pipe-"></a>[WF] Pipe |

<table>
  <tr><td>
<strong>[WF] Pipe |</strong><br/>
Reference for Pipe |.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Pipe |.

#### Related Terms
- Pipe |

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The | pipe operator can be used to chain processes, operators, and workflows:</li>
  <li>The above snippet defines a process named greet and invokes it with the input channel.</li>
  <li>The result is then piped to the map operator, which converts each string to uppercase, and finally to the view operator which prints it.</li>
  <li>The same code can also be written as:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-publishing-files"></a>[WF] Publishing files

<table>
  <tr><td>
<strong>[WF] Publishing files</strong><br/>
Reference for Publishing files.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Publishing files.

#### Related Terms
- Publishing files

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The top-level output directory of a workflow run can be set using the -output-dir command-line option or the outputDir config option:</li>
  <li>The default output directory is results in the launch directory.</li>
  <li>By default, all output files are published to the output directory.</li>
  <li>Each output in the output block can define where files are published using the path directive.</li>
  <li>For example:</li>
  <li>The following directory structure will be created:</li>
  <li>All files received by an output will be published into the specified directory.</li>
  <li>Lists and maps are recursively scanned for nested files.</li>
  <li>The path directive can also be a closure which defines a custom publish path for each channel value:</li>
  <li>The above example will publish each channel value to a different subdirectory.</li>
  <li>In this case, each pair of FASTQ files will be published to a subdirectory based on the sample ID.</li>
  <li>The closure can even define a different path for each individual file using the &gt;&gt; operator:</li>
  <li>Each &gt;&gt; specifies a source file and publish target .</li>
  <li>If the publish target ends with a slash, it is treated as the directory in which source files are published.</li>
  <li>Otherwise, it is treated as the target filename of a source file.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The source file should be a file or collection of files, and the publish target should be a directory or file name.</li>
  <li>Only files that are published with the &gt;&gt; operator are saved to the output directory.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-special-operators"></a>[WF] Special operators

<table>
  <tr><td>
<strong>[WF] Special operators</strong><br/>
The following operators have a special meaning when used in a workflow with
process and workflow calls.<br/>
  </td></tr>
</table>

**At a glance:** The following operators have a special meaning when used in a
workflow with process and workflow calls.

#### Related Terms
- Special operators

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following operators have a special meaning when used in a workflow with process and workflow calls.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="workflow-takes-and-emits"></a>[WF] Takes and emits

<table>
  <tr><td>
<strong>[WF] Takes and emits</strong><br/>
Reference for Takes and emits.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Takes and emits.

#### Related Terms
- Takes and emits

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The take: section is used to declare the inputs of a named workflow:</li>
  <li>Inputs can be specified like arguments when calling the workflow:</li>
  <li>The emit: section is used to declare the outputs of a named workflow:</li>
  <li>When calling the workflow, the output can be accessed using the out property, i.e.</li>
  <li>my_workflow.out .</li>
  <li>If an output is assigned to a name, the name can be used to reference the output from the calling workflow.</li>
  <li>For example:</li>
  <li>The result of the above workflow can be accessed using my_workflow.out.my_data .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [PR] Process

### <a id="process-modules"></a>[PR] Modules

<table>
  <tr><td>
<strong>[PR] Modules</strong><br/>
Environment Modules is a package manager that allows you to dynamically
configure your execution environment and easily switch between multiple versions
of the same software tool.<br/>
  </td></tr>
</table>

**At a glance:** Environment Modules is a package manager that allows you to
dynamically configure your execution environment and easily switch between
multiple versions of the same software tool.

#### Related Terms
- module
- Module inclusion
- Module directory
- Module aliases
- Module parameters
- Module templates
- Module binaries

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Environment Modules is a package manager that allows you to dynamically configure your execution environment and easily switch between multiple versions of the same software tool.</li>
  <li>If it is available in your system you can use it with Nextflow in order to configure the processes execution environment in your pipeline.</li>
  <li>In a process definition you can use the module directive to load a specific module version to be used in the process execution environment.</li>
  <li>For example:</li>
  <li>You can repeat the module directive for each module you need to load.</li>
  <li>Alternatively multiple modules can be specified in a single module directive by separating all the module names by using a : (colon) character as shown below:</li>
  <li>You can include any definition from a module into a Nextflow script using the include keyword.</li>
  <li>The above snippet imports a process named cat , defined in the module, into the main execution context.</li>
  <li>This way, cat can be invoked in the workflow scope.</li>
  <li>Nextflow implicitly looks for the script file ./some/module.nf , resolving the path against the including script location.</li>
  <li>Module includes are subject to the following rules:</li>
  <li>A module can be defined as a directory with the same name as the module and with a script named main.nf .</li>
  <li>Module directories allow the use of module scoped binaries scripts.</li>
  <li>See [Module binaries] for details.</li>
  <li>When including definition from a module, it&#x27;s possible to specify an alias with the as keyword.</li>
  <li>Aliasing allows you to avoid module name clashes, by assigning them different names in the including context.</li>
  <li>You can also include the same definition multiple times under different names:</li>
  <li>A module can define parameters using the same syntax as a Nextflow workflow script:</li>
  <li>When including a module, the module will first use parameters from the including context.</li>
  <li>The above snippet prints:</li>
  <li>The addParams option can be used to pass parameters to the module without adding them to the including scope.</li>
  <li>Alternatively, the params option can be used to pass parameters to module without adding them to the including scope, and without inheriting any parameters from the including scope.</li>
  <li>Process script templates can be included alongside a module in the templates directory.</li>
  <li>For example, suppose we have a project L with a module that defines two processes, P1 and P2, both of which use templates.</li>
  <li>The template files can be made available in the local templates directory:</li>
  <li>Then, we have a second project A with a workflow that includes P1 and P2:</li>
  <li>Finally, we have a third project B with a workflow that also includes P1 and P2:</li>
  <li>With the possibility to keep the template files inside the project L, A and B can use the modules defined in L without any changes.</li>
  <li>A future project C would do the same, just cloning L (if not available on the system) and including its module.</li>
  <li>Beside promoting the sharing of modules across pipelines, there are several advantages to keeping the module template under the script path:</li>
  <li>Having multiple template locations enables a structured project organization.</li>
  <li>If a project has several modules, and they all use templates, the project could group module scripts and their templates as needed.</li>
  <li>Modules can define binary scripts that are locally scoped to the processes defined by the tasks.</li>
  <li>To enable this feature, set the following flag in your pipeline script or configuration file:</li>
  <li>Those scripts will be made accessible like any other command in the task environment, provided they have been granted the Linux execute permissions.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>When defined as a directory, the module must be included by specifying the module directory path:</li>
  <li>The binary scripts must be placed in the module directory names &lt;module-dir&gt;/resources/usr/bin :</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Relative paths must begin with the ./ prefix.</li>
  <li>Include statements are not allowed from within a workflow. They must occur at the script level.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-accelerator"></a>[PR] accelerator

<table>
  <tr><td>
<strong>[PR] accelerator</strong><br/>
The accelerator directive allows you to request hardware accelerators (e.g.<br/>
  </td></tr>
</table>

**At a glance:** The accelerator directive allows you to request hardware
accelerators (e.g.

#### Related Terms
- accelerator

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The accelerator directive allows you to request hardware accelerators (e.g.</li>
  <li>GPUs) for the task execution.</li>
  <li>For example:</li>
  <li>The above examples will request 4 GPUs of type nvidia-tesla-k80 .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-afterscript"></a>[PR] afterScript

<table>
  <tr><td>
<strong>[PR] afterScript</strong><br/>
The afterScript directive allows you to execute a custom (Bash) snippet
immediately after the main process has run.<br/>
  </td></tr>
</table>

**At a glance:** The afterScript directive allows you to execute a custom (Bash)
snippet immediately after the main process has run.

#### Related Terms
- afterScript

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The afterScript directive allows you to execute a custom (Bash) snippet immediately after the main process has run.</li>
  <li>This may be useful to clean up your staging area.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-arch"></a>[PR] arch

<table>
  <tr><td>
<strong>[PR] arch</strong><br/>
The arch directive allows you to define the CPU architecture to build the
software in use by the processa task.<br/>
  </td></tr>
</table>

**At a glance:** The arch directive allows you to define the CPU architecture to
build the software in use by the processa task.

#### Related Terms
- arch

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The arch directive allows you to define the CPU architecture to build the software in use by the processa task.</li>
  <li>For example:</li>
  <li>The example above declares that the CPU generic architecture is linux/x86_64 (X86 64 bit), and more specifically that the microarchitecture is cascadelake (a specific generation of Intel CPUs).</li>
  <li>This directive is currently used by the following Nextflow functionalities:</li>
  <li>Allowed values for the arch directive are as follows, grouped by equivalent family (choices available for the sake of compatibility):</li>
  <li>Examples of values for the architecture target option are cascadelake , icelake , zen2 and zen3 .</li>
  <li>See the Spack documentation for the full and up-to-date list of meaningful targets.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>by the spack directive, to build microarchitecture-optimised applications;</li>
  <li>by the Wave containers service, to build containers for one of the generic families of CPU architectures (see below);</li>
  <li>by the spack strategy within Wave containers , to optimise the container builds for specific CPU microarchitectures.</li>
  <li>X86 64 bit: linux/x86_64 , x86_64 , linux/amd64 , amd64</li>
  <li>ARM 64 bit: linux/aarch64 , aarch64 , linux/arm64 , arm64 , linux/arm64/v8</li>
  <li>ARM 64 bit, older generation: linux/arm64/v7</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-array"></a>[PR] array

<table>
  <tr><td>
<strong>[PR] array</strong><br/>
The array directive allows you to submit tasks as job arrays for executors that
support it.<br/>
  </td></tr>
</table>

**At a glance:** The array directive allows you to submit tasks as job arrays
for executors that support it.

#### Related Terms
- array

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The array directive allows you to submit tasks as job arrays for executors that support it.</li>
  <li>A job array is a collection of jobs with the same resource requirements and the same script (parameterized by an index).</li>
  <li>Job arrays incur significantly less scheduling overhead compared to individual jobs, and as a result they are preferred by HPC schedulers where possible.</li>
  <li>For example:</li>
  <li>Nextflow currently supports job arrays for the following executors:</li>
  <li>A process using job arrays will collect tasks and submit each batch as a job array when it is ready.</li>
  <li>Any aleftovera tasks will be submitted as a partial job array.</li>
  <li>Once a job array is submitted, each achilda task is executed as an independent job.</li>
  <li>Any tasks that fail (and can be retried) will be retried without interfering with the tasks that succeeded.</li>
  <li>Retried tasks are submitted individually rather than through a job array, in order to allow for the use of dynamic resources .</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The directive should be specified with a given array size, along with an executor that supports job arrays.</li>
  <li>The following directives must be uniform across all tasks in a process that uses job arrays, because these directives are specified once for the entire job array:</li>
  <li>For cloud-based executors like AWS Batch, or when using Fusion with any executor, the following additional directives must be uniform:</li>
  <li>When using Wave, the following additional directives must be uniform:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>AWS Batch</li>
  <li>Google Cloud Batch</li>
  <li>LSF</li>
  <li>PBS/Torque</li>
  <li>PBS Pro</li>
  <li>SGE</li>
  <li>SLURM</li>
  <li>accelerator</li>
  <li>clusterOptions</li>
  <li>cpus</li>
  <li>disk</li>
  <li>machineType</li>
  <li>memory</li>
  <li>queue</li>
  <li>resourceLabels</li>
  <li>resourceLimits</li>
  <li>time</li>
  <li>container</li>
  <li>containerOptions</li>
  <li>conda</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-beforescript"></a>[PR] beforeScript

<table>
  <tr><td>
<strong>[PR] beforeScript</strong><br/>
The beforeScript directive allows you to execute a custom (Bash) snippet before
the main process script is run.<br/>
  </td></tr>
</table>

**At a glance:** The beforeScript directive allows you to execute a custom
(Bash) snippet before the main process script is run.

#### Related Terms
- beforeScript

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The beforeScript directive allows you to execute a custom (Bash) snippet before the main process script is run.</li>
  <li>This may be useful to initialise the underlying cluster environment or for other custom initialisation.</li>
  <li>For example:</li>
  <li>cloud batch executors, Kubernetes).</li>
  <li>Otherwise, the beforeScript will be executed outside the container.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>When the process is containerized (using the container directive), the beforeScript will be executed in the container only if the executor is container-native (e.g.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-cache"></a>[PR] cache

<table>
  <tr><td>
<strong>[PR] cache</strong><br/>
The cache directive allows you to store the process results to a local
cache.<br/>
  </td></tr>
</table>

**At a glance:** The cache directive allows you to store the process results to
a local cache.

#### Related Terms
- cache

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The cache directive allows you to store the process results to a local cache.</li>
  <li>When the cache is enabled and the pipeline is launched with the resume option, any task executions that are already cached will be re-used.</li>
  <li>See the Caching and resuming page for more information about how the cache works.</li>
  <li>The cache is enabled by default, but you can disable it for a specific process by setting the cache directive to false .</li>
  <li>For example:</li>
  <li>The following options are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-clusteroptions"></a>[PR] clusterOptions

<table>
  <tr><td>
<strong>[PR] clusterOptions</strong><br/>
The clusterOptions directive allows the usage of any native configuration option
accepted by your cluster submit command.<br/>
  </td></tr>
</table>

**At a glance:** The clusterOptions directive allows the usage of any native
configuration option accepted by your cluster submit command.

#### Related Terms
- clusterOptions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The clusterOptions directive allows the usage of any native configuration option accepted by your cluster submit command.</li>
  <li>You can use it to request non-standard resources or use settings that are specific to your cluster and not supported out of the box by Nextflow.</li>
  <li>The cluster options can be a string:</li>
  <li>The cluster options can also be a string list:</li>
  <li>Grid executors that require one option per line will write each option to a separate line, while grid executors that allow multiple options per line will write all options to a single line, the same as with a string.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>This form is useful to control how the options are split across lines when it is required by the scheduler.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-conda"></a>[PR] conda

<table>
  <tr><td>
<strong>[PR] conda</strong><br/>
The conda directive allows for the definition of the process dependencies using
the Conda package manager.<br/>
  </td></tr>
</table>

**At a glance:** The conda directive allows for the definition of the process
dependencies using the Conda package manager.

#### Related Terms
- conda

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The conda directive allows for the definition of the process dependencies using the Conda package manager.</li>
  <li>Nextflow automatically sets up an environment for the given package names listed by in the conda directive.</li>
  <li>For example:</li>
  <li>Multiple packages can be specified separating them with a blank space e.g.</li>
  <li>bwa=0.7.15 fastqc=0.11.5 .</li>
  <li>The name of the channel from where a specific package needs to be downloaded can be specified using the usual Conda notation i.e.</li>
  <li>prefixing the package with the channel name as shown here bioconda::bwa=0.7.15 .</li>
  <li>The conda directive also allows the specification of a Conda environment file path or the path of an existing environment directory.</li>
  <li>See the Conda environments page for further details.</li>
  <li>The conda scope controls the creation of Conda environments by the Conda package manager.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-container"></a>[PR] container

<table>
  <tr><td>
<strong>[PR] container</strong><br/>
The container directive allows you to execute the process script in a Docker
container.<br/>
  </td></tr>
</table>

**At a glance:** The container directive allows you to execute the process
script in a Docker container.

#### Related Terms
- container

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The container directive allows you to execute the process script in a Docker container.</li>
  <li>It requires the Docker daemon to be running in machine where the pipeline is executed, i.e.</li>
  <li>the local machine when using the local executor or the cluster nodes when the pipeline is deployed through a grid executor.</li>
  <li>For example:</li>
  <li>Simply replace in the above script dockerbox:tag with the name of the Docker image you want to use.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-containeroptions"></a>[PR] containerOptions

<table>
  <tr><td>
<strong>[PR] containerOptions</strong><br/>
The containerOptions directive allows you to specify any container execution
option supported by the underlying container engine (ie.<br/>
  </td></tr>
</table>

**At a glance:** The containerOptions directive allows you to specify any
container execution option supported by the underlying container engine (ie.

#### Related Terms
- containerOptions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The containerOptions directive allows you to specify any container execution option supported by the underlying container engine (ie.</li>
  <li>Docker, Singularity, etc).</li>
  <li>mount a custom path:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>This can be useful to provide container settings only for a specific process e.g.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-cpus"></a>[PR] cpus

<table>
  <tr><td>
<strong>[PR] cpus</strong><br/>
Reference for cpus.<br/>
  </td></tr>
</table>

**At a glance:** Reference for cpus.

#### Related Terms
- cpus

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>For example:</li>
  <li>See also: penv , memory , time , queue , maxForks</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The cpus directive allows you to define the number of (logical) CPU required by the processa task.</li>
  <li>This directive is required for tasks that execute multi-process or multi-threaded commands/tools and it is meant to reserve enough CPUs when a pipeline task is executed through a cluster resource manager.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-debug"></a>[PR] debug

<table>
  <tr><td>
<strong>[PR] debug</strong><br/>
By default the stdout produced by the commands executed in all processes is
ignored.<br/>
  </td></tr>
</table>

**At a glance:** By default the stdout produced by the commands executed in all
processes is ignored.

#### Related Terms
- debug

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>By default the stdout produced by the commands executed in all processes is ignored.</li>
  <li>By setting the debug directive to true , you can forward the process stdout to the current top running process stdout file, showing it in the shell terminal.</li>
  <li>For example:</li>
  <li>Without specifying debug true , you won&#x27;t see the Hello string printed out when executing the above example.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-directives"></a>[PR] Directives

<table>
  <tr><td>
<strong>[PR] Directives</strong><br/>
Reference for Directives.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Directives.

#### Related Terms
- Directives

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-disk"></a>[PR] disk

<table>
  <tr><td>
<strong>[PR] disk</strong><br/>
The disk directive allows you to define how much local disk storage the process
is allowed to use.<br/>
  </td></tr>
</table>

**At a glance:** The disk directive allows you to define how much local disk
storage the process is allowed to use.

#### Related Terms
- disk

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The disk directive allows you to define how much local disk storage the process is allowed to use.</li>
  <li>For example:</li>
  <li>The following memory unit suffix can be used when specifying the disk value:</li>
  <li>See MemoryUnit for more information.</li>
  <li>See also: cpus , memory time , queue and Dynamic task resources .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-echo"></a>[PR] echo

<table>
  <tr><td>
<strong>[PR] echo</strong><br/>
Reference for echo.<br/>
  </td></tr>
</table>

**At a glance:** Reference for echo.

#### Related Terms
- echo

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-errorstrategy"></a>[PR] errorStrategy

<table>
  <tr><td>
<strong>[PR] errorStrategy</strong><br/>
The errorStrategy directive allows you to define how the process manages an
error condition.<br/>
  </td></tr>
</table>

**At a glance:** The errorStrategy directive allows you to define how the
process manages an error condition.

#### Related Terms
- errorStrategy

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The errorStrategy directive allows you to define how the process manages an error condition.</li>
  <li>By default, when an error status is returned by the executed script (i.e.</li>
  <li>when it ends with a non-zero exit status), the process stops immediately, forcing the entire pipeline to terminate.</li>
  <li>The following error strategies are available:</li>
  <li>When setting the errorStrategy directive to ignore the process doesn&#x27;t stop on an error condition, it just reports a message notifying you of the error event.</li>
  <li>For example:</li>
  <li>In this case, the workflow will complete successfully and return an exit status of 0.</li>
  <li>However, if you set workflow.failOnIgnore = true in your Nextflow configuration, the workflow will return a non-zero exit status and report the failed tasks as an error.</li>
  <li>The retry error strategy allows you to re-submit for execution a process returning an error condition.</li>
  <li>The number of times a failing process is re-executed is defined by the maxRetries and maxErrors directives.</li>
  <li>See also: maxErrors , maxRetries and Dynamic task resources .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-executor"></a>[PR] executor

<table>
  <tr><td>
<strong>[PR] executor</strong><br/>
The executor defines the underlying system where processes are executed.<br/>
  </td></tr>
</table>

**At a glance:** The executor defines the underlying system where processes are
executed.

#### Related Terms
- executor

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The executor defines the underlying system where processes are executed.</li>
  <li>By default a process uses the executor defined globally in the nextflow.config file.</li>
  <li>The executor directive allows you to configure what executor has to be used by the process, overriding the default configuration.</li>
  <li>The following executors are available:</li>
  <li>The following example shows how to set the process&#x27;s executor:</li>
  <li>The executor scope controls various executor behaviors.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-ext"></a>[PR] ext

<table>
  <tr><td>
<strong>[PR] ext</strong><br/>
The ext is a special directive used as namespace for user custom process
directives.<br/>
  </td></tr>
</table>

**At a glance:** The ext is a special directive used as namespace for user
custom process directives.

#### Related Terms
- ext

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The ext is a special directive used as namespace for user custom process directives.</li>
  <li>This can be useful for advanced configuration options.</li>
  <li>For example:</li>
  <li>In the above example, the process container version is controlled by ext.version , and the script supports additional command line arguments through ext.args .</li>
  <li>The ext directive can be set in the process definition:</li>
  <li>Or in the Nextflow configuration:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-fair"></a>[PR] fair

<table>
  <tr><td>
<strong>[PR] fair</strong><br/>
The fair directive, when enabled, guarantees that process outputs will be
emitted in the order in which they were received.<br/>
  </td></tr>
</table>

**At a glance:** The fair directive, when enabled, guarantees that process
outputs will be emitted in the order in which they were received.

#### Related Terms
- fair

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The fair directive, when enabled, guarantees that process outputs will be emitted in the order in which they were received.</li>
  <li>For example:</li>
  <li>The above example produces:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-generic-options"></a>[PR] Generic options

<table>
  <tr><td>
<strong>[PR] Generic options</strong><br/>
Reference for Generic options.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Generic options.

#### Related Terms
- Generic options

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following options are available for all process outputs:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs"></a>[PR] Inputs

<table>
  <tr><td>
<strong>[PR] Inputs</strong><br/>
Reference for Inputs.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Inputs.

#### Related Terms
- Inputs

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs-and-outputs-legacy"></a>[PR] Inputs and outputs (legacy)

<table>
  <tr><td>
<strong>[PR] Inputs and outputs (legacy)</strong><br/>
Reference for Inputs and outputs (legacy).<br/>
  </td></tr>
</table>

**At a glance:** Reference for Inputs and outputs (legacy).

#### Related Terms
- Inputs and outputs (legacy)

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-inputs-and-outputs-typed"></a>[PR] Inputs and outputs (typed)

<table>
  <tr><td>
<strong>[PR] Inputs and outputs (typed)</strong><br/>
Reference for Inputs and outputs (typed).<br/>
  </td></tr>
</table>

**At a glance:** Reference for Inputs and outputs (typed).

#### Related Terms
- Inputs and outputs (typed)

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-label"></a>[PR] label

<table>
  <tr><td>
<strong>[PR] label</strong><br/>
The label directive allows the annotation of processes with mnemonic identifier
of your choice.<br/>
  </td></tr>
</table>

**At a glance:** The label directive allows the annotation of processes with
mnemonic identifier of your choice.

#### Related Terms
- label

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The label directive allows the annotation of processes with mnemonic identifier of your choice.</li>
  <li>For example:</li>
  <li>The same label can be applied to more than a process and multiple labels can be applied to the same process using the label directive more than one time.</li>
  <li>Labels are useful to organize workflow processes in separate groups which can be referenced in the configuration file to select and configure a subset of processes having similar computing requirements.</li>
  <li>See Process selectors for more information.</li>
  <li>See also: resourceLabels</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-machinetype"></a>[PR] machineType

<table>
  <tr><td>
<strong>[PR] machineType</strong><br/>
The machineType can be used to specify a predefined Google Compute Platform
machine type when running using the Google Batch , or when using the autopools
feature of the Azure Batch executor .<br/>
  </td></tr>
</table>

**At a glance:** The machineType can be used to specify a predefined Google
Compute Platform machine type when running using the Google Batch , or when
using the autopools feature of the Azure Batch executor .

#### Related Terms
- machineType

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The machineType can be used to specify a predefined Google Compute Platform machine type when running using the Google Batch , or when using the autopools feature of the Azure Batch executor .</li>
  <li>This directive is optional and if specified overrides the cpus and memory directives:</li>
  <li>See also: cpus and memory .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxerrors"></a>[PR] maxErrors

<table>
  <tr><td>
<strong>[PR] maxErrors</strong><br/>
The maxErrors directive allows you to specify the maximum number of times a
process can fail when using the retry error strategy.<br/>
  </td></tr>
</table>

**At a glance:** The maxErrors directive allows you to specify the maximum
number of times a process can fail when using the retry error strategy.

#### Related Terms
- maxErrors

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The maxErrors directive allows you to specify the maximum number of times a process can fail when using the retry error strategy.</li>
  <li>By default this directive is disabled, you can set it as shown in the example below:</li>
  <li>See also: errorStrategy and maxRetries .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxforks"></a>[PR] maxForks

<table>
  <tr><td>
<strong>[PR] maxForks</strong><br/>
The maxForks directive allows you to define the maximum number of process
instances that can be executed in parallel.<br/>
  </td></tr>
</table>

**At a glance:** The maxForks directive allows you to define the maximum number
of process instances that can be executed in parallel.

#### Related Terms
- maxForks

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The maxForks directive allows you to define the maximum number of process instances that can be executed in parallel.</li>
  <li>By default this value is equals to the number of CPU cores available minus 1.</li>
  <li>If you want to execute a process in a sequential manner, set this directive to one.</li>
  <li>For example:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxretries"></a>[PR] maxRetries

<table>
  <tr><td>
<strong>[PR] maxRetries</strong><br/>
The maxRetries directive allows you to define the maximum number of times a
process instance can be re-submitted in case of failure.<br/>
  </td></tr>
</table>

**At a glance:** The maxRetries directive allows you to define the maximum
number of times a process instance can be re-submitted in case of failure.

#### Related Terms
- maxRetries

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The maxRetries directive allows you to define the maximum number of times a process instance can be re-submitted in case of failure.</li>
  <li>See also: errorStrategy and maxErrors .</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>This value is applied only when using the retry error strategy.</li>
  <li>By default only one retry is allowed, you can increase this value as shown below:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-maxsubmitawait"></a>[PR] maxSubmitAwait

<table>
  <tr><td>
<strong>[PR] maxSubmitAwait</strong><br/>
The maxSubmitAwait directive allows you to specify how long a task can remain in
submission queue without being executed.<br/>
  </td></tr>
</table>

**At a glance:** The maxSubmitAwait directive allows you to specify how long a
task can remain in submission queue without being executed.

#### Related Terms
- maxSubmitAwait

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue without being executed.</li>
  <li>Elapsed this time the task execution will fail.</li>
  <li>When used along with retry error strategy, it can be useful to re-schedule the task to a difference queue or resource requirement.</li>
  <li>For example:</li>
  <li>In the above example the task is submitted to the spot-compute on the first attempt ( task.submitAttempt==1 ).</li>
  <li>If the task execution does not start in the 10 minutes, a failure is reported and a new submission is attempted using the queue named on-demand-compute .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-memory"></a>[PR] memory

<table>
  <tr><td>
<strong>[PR] memory</strong><br/>
The memory directive allows you to define how much memory the process is allowed
to use.<br/>
  </td></tr>
</table>

**At a glance:** The memory directive allows you to define how much memory the
process is allowed to use.

#### Related Terms
- memory

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The memory directive allows you to define how much memory the process is allowed to use.</li>
  <li>For example:</li>
  <li>The following memory unit suffix can be used when specifying the memory value:</li>
  <li>See MemoryUnit for more information.</li>
  <li>See also: cpus , time , queue and Dynamic task resources .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-outputs"></a>[PR] Outputs

<table>
  <tr><td>
<strong>[PR] Outputs</strong><br/>
Reference for Outputs.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Outputs.

#### Related Terms
- Outputs

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following functions are available in the output: and topic: sections of a typed process:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-penv"></a>[PR] penv

<table>
  <tr><td>
<strong>[PR] penv</strong><br/>
The penv directive allows you to define the parallel environment to be used when
submitting a parallel task to the SGE resource manager.<br/>
  </td></tr>
</table>

**At a glance:** The penv directive allows you to define the parallel
environment to be used when submitting a parallel task to the SGE resource
manager.

#### Related Terms
- penv

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The penv directive allows you to define the parallel environment to be used when submitting a parallel task to the SGE resource manager.</li>
  <li>For example:</li>
  <li>This configuration depends on the parallel environment provided by your grid engine installation.</li>
  <li>Refer to your cluster documentation or contact your admin to learn more about this.</li>
  <li>See also: cpus , memory , time</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-pod"></a>[PR] pod

<table>
  <tr><td>
<strong>[PR] pod</strong><br/>
The pod directive allows the definition of pod specific settings, such as
environment variables, secrets, and config maps, when using the Kubernetes
executor.<br/>
  </td></tr>
</table>

**At a glance:** The pod directive allows the definition of pod specific
settings, such as environment variables, secrets, and config maps, when using
the Kubernetes executor.

#### Related Terms
- pod

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The pod directive allows the definition of pod specific settings, such as environment variables, secrets, and config maps, when using the Kubernetes executor.</li>
  <li>For example:</li>
  <li>The above snippet defines an environment variable named MESSAGE whose value is &#x27;hello world&#x27; .</li>
  <li>When defined in the Nextflow configuration file, a pod setting can be defined as a map:</li>
  <li>Or as a list of maps:</li>
  <li>The following options are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-publishdir"></a>[PR] publishDir

<table>
  <tr><td>
<strong>[PR] publishDir</strong><br/>
The publishDir directive allows you to publish the process output files to a
specified folder.<br/>
  </td></tr>
</table>

**At a glance:** The publishDir directive allows you to publish the process
output files to a specified folder.

#### Related Terms
- publishDir

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The publishDir directive allows you to publish the process output files to a specified folder.</li>
  <li>For example:</li>
  <li>The above example splits the string Hola into file chunks of a single byte.</li>
  <li>When complete the chunk_* output files are published into the /data/chunks folder.</li>
  <li>By default files are published to the target folder creating a symbolic link for each process output that links the file produced into the process working directory.</li>
  <li>This behavior can be modified using the mode option, for example:</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-queue"></a>[PR] queue

<table>
  <tr><td>
<strong>[PR] queue</strong><br/>
The queue directive allows you to set the queue where jobs are scheduled when
using a grid based executor in your pipeline.<br/>
  </td></tr>
</table>

**At a glance:** The queue directive allows you to set the queue where jobs are
scheduled when using a grid based executor in your pipeline.

#### Related Terms
- queue

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The queue directive allows you to set the queue where jobs are scheduled when using a grid based executor in your pipeline.</li>
  <li>For example:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-resourcelabels"></a>[PR] resourceLabels

<table>
  <tr><td>
<strong>[PR] resourceLabels</strong><br/>
The resourceLabels directive allows you to specify custom name-value pairs that
Nextflow applies to the computing resource used to carry out the process
execution.<br/>
  </td></tr>
</table>

**At a glance:** The resourceLabels directive allows you to specify custom
name-value pairs that Nextflow applies to the computing resource used to carry
out the process execution.

#### Related Terms
- resourceLabels

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies to the computing resource used to carry out the process execution.</li>
  <li>Resource labels can be specified using the syntax shown below:</li>
  <li>Resource labels are currently supported by the following executors:</li>
  <li>See also: label</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The limits and the syntax of the corresponding cloud provider should be taken into consideration when using resource labels.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>AWS Batch</li>
  <li>Azure Batch</li>
  <li>Google Cloud Batch</li>
  <li>Kubernetes</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-resourcelimits"></a>[PR] resourceLimits

<table>
  <tr><td>
<strong>[PR] resourceLimits</strong><br/>
The resourceLimits directive allows you to specify environment-specific limits
for task resource requests.<br/>
  </td></tr>
</table>

**At a glance:** The resourceLimits directive allows you to specify
environment-specific limits for task resource requests.

#### Related Terms
- resourceLimits

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The resourceLimits directive allows you to specify environment-specific limits for task resource requests.</li>
  <li>Resource limits can be specified in a process as follows:</li>
  <li>Or in the Nextflow configuration:</li>
  <li>Resource limits can be defined for the following directives:</li>
  <li>Resource limits are a useful way to specify environment-specific limits alongside tasks with dynamic resources .</li>
  <li>Normally, if a task requests more resources than can be provisioned (e.g.</li>
  <li>a task requests 32 cores but the largest node in the cluster has 24), the task will either fail or cause the pipeline to hang forever as it will never be scheduled.</li>
  <li>If the resourceLimits directive is defined with these limits, the task resources will be automatically reduced to comply with these limits before the job is submitted.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>cpus</li>
  <li>disk</li>
  <li>memory</li>
  <li>time</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-scratch"></a>[PR] scratch

<table>
  <tr><td>
<strong>[PR] scratch</strong><br/>
The scratch directive allows you to execute the process in a temporary folder
that is local to the execution node.<br/>
  </td></tr>
</table>

**At a glance:** The scratch directive allows you to execute the process in a
temporary folder that is local to the execution node.

#### Related Terms
- scratch

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The scratch directive allows you to execute the process in a temporary folder that is local to the execution node.</li>
  <li>This is useful when your pipeline is launched by using a grid executor, because it allows you to decrease the NFS overhead by running the pipeline processes in a temporary directory in the local disk of the actual execution node.</li>
  <li>In its basic form simply specify true at the directive value, as shown below:</li>
  <li>By doing this, it tries to execute the script in the directory defined by the variable $TMPDIR in the execution node.</li>
  <li>If this variable does not exist, it will create a new temporary directory by using the Linux command mktemp .</li>
  <li>Nextflow creates a subdirectory within the scratch directory for each task and automatically deletes it once the task completes.</li>
  <li>The following values are supported:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Only the files declared as output in the process definition will be copied in the pipeline working area.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-secret"></a>[PR] secret

<table>
  <tr><td>
<strong>[PR] secret</strong><br/>
The secret directive allows a process to access secrets.<br/>
  </td></tr>
</table>

**At a glance:** The secret directive allows a process to access secrets.

#### Related Terms
- secret

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The secret directive allows a process to access secrets.</li>
  <li>Secrets can be added to a process as follows:</li>
  <li>See Secrets for more information.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-shell"></a>[PR] shell

<table>
  <tr><td>
<strong>[PR] shell</strong><br/>
The shell directive allows you to define a custom shell command for process
scripts.<br/>
  </td></tr>
</table>

**At a glance:** The shell directive allows you to define a custom shell command
for process scripts.

#### Related Terms
- shell

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The shell directive allows you to define a custom shell command for process scripts.</li>
  <li>By default, script blocks are executed with /bin/bash -ue .</li>
  <li>The same directive could be specified in your Nextflow configuration as follows:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-spack"></a>[PR] spack

<table>
  <tr><td>
<strong>[PR] spack</strong><br/>
The spack directive allows for the definition of the process dependencies using
the Spack package manager.<br/>
  </td></tr>
</table>

**At a glance:** The spack directive allows for the definition of the process
dependencies using the Spack package manager.

#### Related Terms
- spack

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The spack directive allows for the definition of the process dependencies using the Spack package manager.</li>
  <li>Nextflow automatically sets up an environment for the given package names listed by in the spack directive.</li>
  <li>For example:</li>
  <li>Multiple packages can be specified separating them with a blank space, e.g.</li>
  <li>bwa@0.7.15 fastqc@0.11.5 .</li>
  <li>The spack directive also allows the specification of a Spack environment file path or the path of an existing environment directory.</li>
  <li>See the Spack environments page for further details.</li>
  <li>The spack scope controls the creation of a Spack environment by the Spack package manager.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stage-directives"></a>[PR] Stage directives

<table>
  <tr><td>
<strong>[PR] Stage directives</strong><br/>
Reference for Stage directives.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Stage directives.

#### Related Terms
- Stage directives

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following directives can be used in the stage: section of a typed process:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stageinmode"></a>[PR] stageInMode

<table>
  <tr><td>
<strong>[PR] stageInMode</strong><br/>
The stageInMode directive defines how input files are staged into the process
work directory.<br/>
  </td></tr>
</table>

**At a glance:** The stageInMode directive defines how input files are staged
into the process work directory.

#### Related Terms
- stageInMode

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The stageInMode directive defines how input files are staged into the process work directory.</li>
  <li>The following values are allowed:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-stageoutmode"></a>[PR] stageOutMode

<table>
  <tr><td>
<strong>[PR] stageOutMode</strong><br/>
The stageOutMode directive defines how output files are staged out from the
scratch directory to the process work directory.<br/>
  </td></tr>
</table>

**At a glance:** The stageOutMode directive defines how output files are staged
out from the scratch directory to the process work directory.

#### Related Terms
- stageOutMode

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The stageOutMode directive defines how output files are staged out from the scratch directory to the process work directory.</li>
  <li>The following values are allowed:</li>
  <li>See also: scratch .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-storedir"></a>[PR] storeDir

<table>
  <tr><td>
<strong>[PR] storeDir</strong><br/>
The storeDir directive allows you to define a directory that is used as a
permanent cache for your process results.<br/>
  </td></tr>
</table>

**At a glance:** The storeDir directive allows you to define a directory that is
used as a permanent cache for your process results.

#### Related Terms
- storeDir

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The storeDir directive allows you to define a directory that is used as a permanent cache for your process results.</li>
  <li>In more detail, it affects the process execution in two main ways:</li>
  <li>The following example shows how to use the storeDir directive to create a directory containing a BLAST database for each species specified by an input parameter:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-tag"></a>[PR] tag

<table>
  <tr><td>
<strong>[PR] tag</strong><br/>
The tag directive allows you to associate each process execution with a custom
label, so that it will be easier to identify them in the log file or in the
trace execution report.<br/>
  </td></tr>
</table>

**At a glance:** The tag directive allows you to associate each process
execution with a custom label, so that it will be easier to identify them in the
log file or in the trace execution report.

#### Related Terms
- tag

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The tag directive allows you to associate each process execution with a custom label, so that it will be easier to identify them in the log file or in the trace execution report.</li>
  <li>For example:</li>
  <li>The above snippet will print a log similar to the following one, where process names contain the tag value:</li>
  <li>See also Trace execution report</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-task-properties"></a>[PR] Task properties

<table>
  <tr><td>
<strong>[PR] Task properties</strong><br/>
Reference for Task properties.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Task properties.

#### Related Terms
- Task properties

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following task properties are defined in the process body:</li>
  <li>Additionally, the directive values for the given task can be accessed via task.&lt;directive&gt; .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="process-time"></a>[PR] time

<table>
  <tr><td>
<strong>[PR] time</strong><br/>
The time directive allows you to define how long a process is allowed to
run.<br/>
  </td></tr>
</table>

**At a glance:** The time directive allows you to define how long a process is
allowed to run.

#### Related Terms
- time

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The time directive allows you to define how long a process is allowed to run.</li>
  <li>For example:</li>
  <li>The following time unit suffixes can be used when specifying the duration value:</li>
  <li>See Duration for more information.</li>
  <li>See also: cpus , memory , queue and Dynamic task resources .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [CH] Channel

### <a id="channel-empty"></a>[CH] empty

<table>
  <tr><td>
<strong>[CH] empty</strong><br/>
The channel.empty factory method, by definition, creates a channel that
doesn&#x27;t emit any value.<br/>
  </td></tr>
</table>

**At a glance:** The channel.empty factory method, by definition, creates a
channel that doesn't emit any value.

#### Related Terms
- empty

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.empty factory method, by definition, creates a channel that doesn&#x27;t emit any value.</li>
  <li>See also: ifEmpty .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-from"></a>[CH] from

<table>
  <tr><td>
<strong>[CH] from</strong><br/>
Reference for from.<br/>
  </td></tr>
</table>

**At a glance:** Reference for from.

#### Related Terms
- from

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.from method allows you to create a channel emitting any sequence of values that are specified as the method argument, for example:</li>
  <li>The first line in this example creates a variable ch which holds a channel object.</li>
  <li>This channel emits the values specified as a parameter in the from method.</li>
  <li>Thus the second line will print the following:</li>
  <li>The following example shows how to create a channel from a range of numbers or strings:</li>
  <li>Thus the following two declarations produce an identical result even though in the first case the items are specified as multiple arguments while in the second case as a single list object argument:</li>
  <li>But when more than one argument is provided, they are always managed as single emissions.</li>
  <li>Thus, the following example creates a channel emitting three entries each of which is a list containing two elements:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromfilepairs"></a>[CH] fromFilePairs

<table>
  <tr><td>
<strong>[CH] fromFilePairs</strong><br/>
The channel.fromFilePairs method creates a channel emitting the file pairs
matching a glob pattern provided by the user.<br/>
  </td></tr>
</table>

**At a glance:** The channel.fromFilePairs method creates a channel emitting the
file pairs matching a glob pattern provided by the user.

#### Related Terms
- fromFilePairs

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob pattern provided by the user.</li>
  <li>The matching files are emitted as tuples in which the first element is the grouping key of the matching pair and the second element is the list of files (sorted in lexicographical order).</li>
  <li>For example:</li>
  <li>It will produce an output similar to the following:</li>
  <li>Multiple glob patterns can be specified using a list:</li>
  <li>Alternatively, it is possible to implement a custom file pair grouping strategy providing a closure which, given the current file as parameter, returns the grouping key.</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromlineage"></a>[CH] fromLineage

<table>
  <tr><td>
<strong>[CH] fromLineage</strong><br/>
Reference for fromLineage.<br/>
  </td></tr>
</table>

**At a glance:** Reference for fromLineage.

#### Related Terms
- fromLineage

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.fromLineage factory creates a channel that emits files from the lineage store that match the given key-value params:</li>
  <li>The above snippet emits files published by the given workflow run that are labeled as alpha and beta .</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromlist"></a>[CH] fromList

<table>
  <tr><td>
<strong>[CH] fromList</strong><br/>
Reference for fromList.<br/>
  </td></tr>
</table>

**At a glance:** Reference for fromList.

#### Related Terms
- fromList

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.fromList method allows you to create a channel emitting the values provided as a list of elements, for example:</li>
  <li>Prints:</li>
  <li>See also: channel.of factory method.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-frompath"></a>[CH] fromPath

<table>
  <tr><td>
<strong>[CH] fromPath</strong><br/>
You can create a channel emitting one or more file paths by using the
channel.fromPath method and specifying a path string as an argument.<br/>
  </td></tr>
</table>

**At a glance:** You can create a channel emitting one or more file paths by
using the channel.fromPath method and specifying a path string as an argument.

#### Related Terms
- fromPath

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>You can create a channel emitting one or more file paths by using the channel.fromPath method and specifying a path string as an argument.</li>
  <li>For example:</li>
  <li>The above line creates a channel and binds it to a Path object for the specified file.</li>
  <li>Whenever the channel.fromPath argument contains a * or ?</li>
  <li>wildcard character it is interpreted as a glob path matcher.</li>
  <li>This example creates a channel and emits as many Path items as there are files with txt extension in the /data/big folder.</li>
  <li>The first line returns a channel emitting the files ending with the suffix .fa in the data folder and recursively in all its sub-folders.</li>
  <li>Finally the last example emits two files: data/file_1.fq and data/file_2.fq .</li>
  <li>Multiple paths or glob patterns can be specified using a list:</li>
  <li>In order to include hidden files, you need to start your pattern with a period character or specify the hidden: true option.</li>
  <li>The first example returns all hidden files in the specified path.</li>
  <li>The second one returns all hidden files ending with the .fa suffix.</li>
  <li>Finally the last example returns all files (hidden and non-hidden) in that path.</li>
  <li>it won&#x27;t return directory paths.</li>
  <li>You can use the type option specifying the value file , dir or any in order to define what kind of paths you want.</li>
  <li>The first example will return all directory paths ending with the b suffix, while the second will return any file or directory starting with a a prefix.</li>
  <li>Available options:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>While the second one only emits the files which have the same suffix in any sub-folder in the data path.</li>
  <li>By default a glob pattern only looks for regular file paths that match the specified criteria, i.e.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-fromsra"></a>[CH] fromSRA

<table>
  <tr><td>
<strong>[CH] fromSRA</strong><br/>
The channel.fromSRA method queries the NCBI SRA database and returns a channel
emitting the FASTQ files matching the specified criteria i.e project or
accession number(s).<br/>
  </td></tr>
</table>

**At a glance:** The channel.fromSRA method queries the NCBI SRA database and
returns a channel emitting the FASTQ files matching the specified criteria i.e
project or accession number(s).

#### Related Terms
- fromSRA

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ files matching the specified criteria i.e project or accession number(s).</li>
  <li>For example:</li>
  <li>It returns:</li>
  <li>Multiple accession IDs can be specified using a list object:</li>
  <li>This method uses the NCBI ESearch API behind the scenes, therefore it allows the use of any query term supported by this API.</li>
  <li>Available options:</li>
  <li>Available retry policy properties:</li>
  <li>The following code snippet shows an example for using the channel.fromSRA factory method with a custom retryPolicy .</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>To access the ESearch API, you must provide your NCBI API keys through one of the following ways:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>The apiKey option: channel . fromSRA ( ids , apiKey: &#x27;0123456789abcdef&#x27; )</li>
  <li>The NCBI_API_KEY variable in your environment: export NCBI_API_KEY = 0123456789abcdef</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-interval"></a>[CH] interval

<table>
  <tr><td>
<strong>[CH] interval</strong><br/>
The interval method emits an incrementing index (starting from zero) at a
periodic interval.<br/>
  </td></tr>
</table>

**At a glance:** The interval method emits an incrementing index (starting from
zero) at a periodic interval.

#### Related Terms
- interval

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The interval method emits an incrementing index (starting from zero) at a periodic interval.</li>
  <li>For example:</li>
  <li>The above snippet will emit 0, 1, 2, and so on, every second, forever.</li>
  <li>You can use an operator such as take or until to close the channel based on a stopping condition.</li>
  <li>An optional closure can be used to transform the index.</li>
  <li>Additionally, returning channel.STOP will close the channel.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-of"></a>[CH] of

<table>
  <tr><td>
<strong>[CH] of</strong><br/>
Reference for of.<br/>
  </td></tr>
</table>

**At a glance:** Reference for of.

#### Related Terms
- of

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.of method allows you to create a channel that emits the arguments provided to it, for example:</li>
  <li>The first line in this example creates a variable ch which holds a channel object.</li>
  <li>This channel emits the arguments supplied to the of method.</li>
  <li>Thus the second line prints the following:</li>
  <li>Ranges of values are expanded accordingly:</li>
  <li>Prints:</li>
  <li>See also: channel.fromList factory method.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-topic"></a>[CH] topic

<table>
  <tr><td>
<strong>[CH] topic</strong><br/>
A topic channel is a channel that can receive values from many sources
implicitly based on a matching topic name .<br/>
  </td></tr>
</table>

**At a glance:** A topic channel is a channel that can receive values from many
sources implicitly based on a matching topic name .

#### Related Terms
- topic

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A topic channel is a channel that can receive values from many sources implicitly based on a matching topic name .</li>
  <li>A process output can be assigned to a topic using the topic option on an output, for example:</li>
  <li>The channel.topic function returns the topic channel for the given name, which can be used as input to a process or operator, like any other channel:</li>
  <li>This approach is a convenient way to collect related items from many different sources without explicitly connecting them (e.g.</li>
  <li>using the mix operator).</li>
  <li>See also: Generic options for process outputs.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-value"></a>[CH] value

<table>
  <tr><td>
<strong>[CH] value</strong><br/>
The channel.value function creates a dataflow value bound to the given
argument.<br/>
  </td></tr>
</table>

**At a glance:** The channel.value function creates a dataflow value bound to
the given argument.

#### Related Terms
- value

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.value function creates a dataflow value bound to the given argument.</li>
  <li>For example:</li>
  <li>The first line creates a dataflow value bound to the string &#x27;Hello there&#x27; .</li>
  <li>The second line creates a dataflow value bound to the list [1,2,3,4,5] , which is treated as a single value in dataflow logic.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="channel-watchpath"></a>[CH] watchPath

<table>
  <tr><td>
<strong>[CH] watchPath</strong><br/>
The channel.watchPath method watches a folder for one or more files matching a
specified pattern.<br/>
  </td></tr>
</table>

**At a glance:** The channel.watchPath method watches a folder for one or more
files matching a specified pattern.

#### Related Terms
- watchPath

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The channel.watchPath method watches a folder for one or more files matching a specified pattern.</li>
  <li>As soon as there is a file that meets the specified condition, it is emitted over the channel that is returned by the watchPath method.</li>
  <li>The condition on files to watch can be specified by using * or ?</li>
  <li>wildcard characters i.e.</li>
  <li>by specifying a glob path matching criteria.</li>
  <li>For example:</li>
  <li>Optionally, it is possible to provide a second argument that specifies what event(s) to watch.</li>
  <li>The supported events are:</li>
  <li>You can specify more than one of these events by using a comma separated string as shown below:</li>
  <li>See also: channel.fromPath factory method.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>By default it watches only for new files created in the specified folder.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>create : A new file is created (default)</li>
  <li>modify : A file is modified</li>
  <li>delete : A file is deleted</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [OP] Operator

### <a id="operator-branch"></a>[OP] branch

<table>
  <tr><td>
<strong>[OP] branch</strong><br/>
Returns: multiple channels<br/>
  </td></tr>
</table>

**At a glance:** Returns: multiple channels

#### Related Terms
- branch

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: multiple channels</li>
  <li>The branch operator forwards each item from a source channel to one of multiple output channels, based on a selection criteria.</li>
  <li>The selection criteria is a closure that defines, for each output channel, a unique label followed by a boolean expression.</li>
  <li>When an item is received, it is routed to the first output channel whose expression evaluates to true .</li>
  <li>For example:</li>
  <li>A fallback condition can be specified using true as the last branch condition:</li>
  <li>The value emitted to each branch can be customized with an expression statement (or statements) after the branch condition:</li>
  <li>The branchCriteria() method can be used to create a branch criteria as a variable that can be passed as an argument to any number of branch operations, as shown below:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-buffer"></a>[OP] buffer

<table>
  <tr><td>
<strong>[OP] buffer</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- buffer

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The buffer operator collects items from a source channel into subsets and emits each subset separately.</li>
  <li>This operator has multiple variants:</li>
  <li>See also: collate</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collate"></a>[OP] collate

<table>
  <tr><td>
<strong>[OP] collate</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- collate

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The collate operator collects items from a source channel into groups of N items.</li>
  <li>This operator has multiple variants:</li>
  <li>See also: buffer</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collect"></a>[OP] collect

<table>
  <tr><td>
<strong>[OP] collect</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- collect

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The collect operator collects all items from a source channel into a list and emits it as a single item:</li>
  <li>An optional closure can be used to transform each item before it is collected:</li>
  <li>Available options:</li>
  <li>See also: toList , toSortedList</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-collectfile"></a>[OP] collectFile

<table>
  <tr><td>
<strong>[OP] collectFile</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- collectFile

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The collectFile operator collects the items from a source channel and saves them to one or more files, emitting the collected file(s).</li>
  <li>This operator has multiple variants:</li>
  <li>The following example shows how to use a closure to collect and sort all sequences in a FASTA file from shortest to longest:</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-combine"></a>[OP] combine

<table>
  <tr><td>
<strong>[OP] combine</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- combine

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The combine operator produces the combinations (i.e.</li>
  <li>cross product, Cartesian product) of two source channels, or a channel and a list (as the right operand), emitting each combination separately.</li>
  <li>For example:</li>
  <li>The by option can be used to combine items that share a matching key.</li>
  <li>See also: cross , join</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The value should be the zero-based index of the tuple, or a list of indices.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-concat"></a>[OP] concat

<table>
  <tr><td>
<strong>[OP] concat</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- concat

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The concat operator emits the items from two or more source channels into a single output channel.</li>
  <li>Each source channel is emitted in the order in which it was specified.</li>
  <li>For example:</li>
  <li>See also: mix</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>In other words, given N channels, the items from the i+1 -th channel are emitted only after all of the items from the i -th channel have been emitted.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-count"></a>[OP] count

<table>
  <tr><td>
<strong>[OP] count</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- count

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The count operator computes the total number of items in a source channel and emits it:</li>
  <li>An optional filter can be provided to select which items to count.</li>
  <li>The selection criteria can be a literal value, a regular expression , a type qualifier (i.e.</li>
  <li>Java class), or a boolean predicate.</li>
  <li>For example:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countfasta"></a>[OP] countFasta

<table>
  <tr><td>
<strong>[OP] countFasta</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- countFasta

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>Counts the total number of records in a channel of FASTA files, equivalent to splitFasta | count .</li>
  <li>See splitFasta for the list of available options.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countfastq"></a>[OP] countFastq

<table>
  <tr><td>
<strong>[OP] countFastq</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- countFastq

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>Counts the total number of records in a channel of FASTQ files, equivalent to splitFastq | count .</li>
  <li>See splitFastq for the list of available options.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countjson"></a>[OP] countJson

<table>
  <tr><td>
<strong>[OP] countJson</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- countJson

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>Counts the total number of records in a channel of JSON files, equivalent to splitJson | count .</li>
  <li>See splitJson for the list of available options.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-countlines"></a>[OP] countLines

<table>
  <tr><td>
<strong>[OP] countLines</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- countLines

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>Counts the total number of lines in a channel of text files, equivalent to splitText | count .</li>
  <li>See splitLines for the list of available options.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-cross"></a>[OP] cross

<table>
  <tr><td>
<strong>[OP] cross</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- cross

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The cross operator emits every pairwise combination of two channels for which the pair has a matching key.</li>
  <li>By default, the key is defined as the first entry in a list or map, or the value itself for any other data type.</li>
  <li>For example:</li>
  <li>An optional closure can be used to define the matching key for each item:</li>
  <li>There are two important caveats when using the cross operator:</li>
  <li>See also: combine</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-distinct"></a>[OP] distinct

<table>
  <tr><td>
<strong>[OP] distinct</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- distinct

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The distinct operator forwards a source channel with consecutively repeated items removed, such that each emitted item is different from the preceding one:</li>
  <li>An optional closure can be used to transform each value before it is evaluated for distinct-ness:</li>
  <li>See also: unique</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-dump"></a>[OP] dump

<table>
  <tr><td>
<strong>[OP] dump</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- dump

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The dump operator prints each item in a source channel when the pipeline is executed with the -dump-channels command-line option, otherwise it does nothing.</li>
  <li>It is a useful way to inspect and debug channels quickly without having to modify the pipeline script.</li>
  <li>The tag option can be used to select which channels to dump:</li>
  <li>Then, you can run your pipeline with -dump-channels plus1 or -dump-channels exp2 to dump the content of either channel.</li>
  <li>Multiple tag names can be specified as a comma-separated list.</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-filter"></a>[OP] filter

<table>
  <tr><td>
<strong>[OP] filter</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- filter

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The filter operator emits the items from a source channel that satisfy a condition, discarding all other items.</li>
  <li>The filter condition can be a literal value, a regular expression , a type qualifier (i.e.</li>
  <li>Java class), or a boolean predicate.</li>
  <li>The following example filters a channel using a boolean predicate, which is a closure that returns a boolean value.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The following example filters a channel with a regular expression that only matches strings beginning with a :</li>
  <li>The following example filters a channel with the Number type qualifier so that only numbers are emitted:</li>
  <li>In this case, the predicate is used to select only odd numbers:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-first"></a>[OP] first

<table>
  <tr><td>
<strong>[OP] first</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- first

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The first operator emits the first item in a source channel, or the first item that matches a condition.</li>
  <li>The condition can be a regular expression , a type qualifier (i.e.</li>
  <li>Java class), or a boolean predicate.</li>
  <li>For example:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-flatmap"></a>[OP] flatMap

<table>
  <tr><td>
<strong>[OP] flatMap</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- flatMap

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The flatMap operator applies a mapping function to each item from a source channel.</li>
  <li>When the mapping function returns a list, each element in the list is emitted separately:</li>
  <li>When the mapping function returns a map, each key-value pair in the map is emitted separately:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-flatten"></a>[OP] flatten

<table>
  <tr><td>
<strong>[OP] flatten</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- flatten

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The flatten operator flattens each item from a source channel that is a list or other collection, such that each element in each collection is emitted separately:</li>
  <li>As shown in the above example, deeply nested collections are also flattened.</li>
  <li>See also: flatMap</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-grouptuple"></a>[OP] groupTuple

<table>
  <tr><td>
<strong>[OP] groupTuple</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- groupTuple

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The groupTuple operator collects lists (i.e.</li>
  <li>tuples ) from a source channel into groups based on a grouping key.</li>
  <li>A new tuple is emitted for each distinct key.</li>
  <li>To be more precise, the operator transforms a sequence of tuples like (K, V, W, ..) into a sequence of tuples like (K, list(V), list(W), ..) .</li>
  <li>For example:</li>
  <li>By default, the first element of each tuple is used as the grouping key.</li>
  <li>The by option can be used to specify a different index, or list of indices.</li>
  <li>For example, to group by the second element of each tuple:</li>
  <li>By default, if you don&#x27;t specify a size, the groupTuple operator will not emit any groups until all inputs have been received.</li>
  <li>In cases where the size of each group varies based on the grouping key, you can use the built-in groupKey() function, which allows you to define a different expected size for each group:</li>
  <li>Available options:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>If possible, you should always try to specify the number of expected elements in each group using the size option, so that each group can be emitted as soon as it&#x27;s ready.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-ifempty"></a>[OP] ifEmpty

<table>
  <tr><td>
<strong>[OP] ifEmpty</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- ifEmpty

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The ifEmpty operator emits a source channel, or a default value if the source channel is empty (doesn&#x27;t emit any value):</li>
  <li>The default value can also be a closure , in which case the closure is evaluated and the result is emitted when the source channel is empty.</li>
  <li>See also: empty channel factory</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-join"></a>[OP] join

<table>
  <tr><td>
<strong>[OP] join</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- join

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The join operator emits the inner product of two source channels using a matching key.</li>
  <li>To be more precise, the operator transforms a sequence of tuples like (K, V1, V2, ..) and (K, W1, W1, ..) into a sequence of tuples like (K, V1, V2, .., W1, W2, ..) .</li>
  <li>For example:</li>
  <li>By default, the first element of each item is used as the key.</li>
  <li>The by option can be used to specify a different index, or list of indices.</li>
  <li>By default, unmatched items are discarded.</li>
  <li>The remainder option can be used to emit them at the end:</li>
  <li>Available options:</li>
  <li>See also: combine , cross</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-last"></a>[OP] last

<table>
  <tr><td>
<strong>[OP] last</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- last

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The last operator emits the last item from a source channel:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-map"></a>[OP] map

<table>
  <tr><td>
<strong>[OP] map</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- map

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The map operator applies a mapping function to each item from a source channel:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-max"></a>[OP] max

<table>
  <tr><td>
<strong>[OP] max</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- max

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The max operator emits the item with the greatest value from a source channel:</li>
  <li>An optional closure can be used to control how the items are compared.</li>
  <li>The closure can be a mapping function , which transforms each item before it is compared, or a comparator function , which defines how to compare two items more generally.</li>
  <li>The following examples show how to find the longest string in a channel:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-merge"></a>[OP] merge

<table>
  <tr><td>
<strong>[OP] merge</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- merge

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The merge operator joins the items from two or more channels into a new channel:</li>
  <li>An optional closure can be used to control how two items are merged:</li>
  <li>The merge operator may return a channel or value depending on the inputs:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>If the first argument is a channel, the merge operator returns a channel merging as many values as are available for all inputs. Dataflow values are re-used for each merged value.</li>
  <li>If the first argument is a dataflow value, the merge operator returns a dataflow value, merging the first value from each input, regardless of whether there are channel inputs with additional values.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-min"></a>[OP] min

<table>
  <tr><td>
<strong>[OP] min</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- min

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The min operator emits the item with the lowest value from a source channel:</li>
  <li>An optional closure can be used to control how the items are compared.</li>
  <li>The closure can be a mapping function , which transforms each item before it is compared, or a comparator function , which defines how to compare two items more generally.</li>
  <li>The following examples show how to find the shortest string in a channel:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-mix"></a>[OP] mix

<table>
  <tr><td>
<strong>[OP] mix</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- mix

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The mix operator emits the items from two or more source channels into a single output channel:</li>
  <li>The items in the mixed output channel may appear in any order, regardless of which source channel they came from.</li>
  <li>Thus, the previous example could also output the following:</li>
  <li>See also: concat</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-multimap"></a>[OP] multiMap

<table>
  <tr><td>
<strong>[OP] multiMap</strong><br/>
Returns: multiple channels<br/>
  </td></tr>
</table>

**At a glance:** Returns: multiple channels

#### Related Terms
- multiMap

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: multiple channels</li>
  <li>The multiMap operator applies a set of mapping functions to a source channel, producing a separate output channel for each mapping function.</li>
  <li>The multi-map criteria is a closure that defines, for each output channel, a label followed by a mapping expression.</li>
  <li>For example:</li>
  <li>Multiple labels can share the same mapping expression using the following shorthand:</li>
  <li>The above example creates two channels as before, but now they both receive the same items.</li>
  <li>You can use the multiMapCriteria() method to create a multi-map criteria as a variable that can be passed as an argument to any number of multiMap operations, as shown below:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-randomsample"></a>[OP] randomSample

<table>
  <tr><td>
<strong>[OP] randomSample</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- randomSample

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The randomSample operator emits a randomly-selected subset of items from a source channel:</li>
  <li>The above snippet will print 10 randomly-selected numbers between 1 and 100 (without replacement).</li>
  <li>An optional second parameter can be used to set the initial seed for the random number generator, which ensures that the randomSample operator produces the same pseudo-random sequence across runs:</li>
  <li>The above example will print 10 randomly-selected numbers between 1 and 100 (without replacement).</li>
  <li>Each subsequent script execution will produce the same sequence.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-reduce"></a>[OP] reduce

<table>
  <tr><td>
<strong>[OP] reduce</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- reduce

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The reduce operator applies an accumulator function sequentially to each item in a source channel, and emits the final accumulated value.</li>
  <li>This process is repeated for each item in the source channel.</li>
  <li>For example:</li>
  <li>By default, the first item is used as the initial accumulated value.</li>
  <li>You can optionally specify a different initial value as shown below:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The accumulator function takes two parameters a the accumulated value and the i -th emitted item a and it should return the accumulated result, which is passed to the next invocation with the i+1 -th item.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-set"></a>[OP] set

<table>
  <tr><td>
<strong>[OP] set</strong><br/>
Returns: nothing<br/>
  </td></tr>
</table>

**At a glance:** Returns: nothing

#### Related Terms
- set

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: nothing</li>
  <li>The set operator assigns a source channel to a variable, whose name is specified as a closure parameter:</li>
  <li>Using set is semantically equivalent to assigning a variable:</li>
  <li>See also: tap</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitcsv"></a>[OP] splitCsv

<table>
  <tr><td>
<strong>[OP] splitCsv</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- splitCsv

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The splitCsv operator parses and splits CSV files or text from a source channel into records.</li>
  <li>For example:</li>
  <li>The above example shows hows CSV text is parsed and split into individual rows, where each row is simply a list of columns.</li>
  <li>When the CSV begins with a header line defining the column names, and the header option is true , each row is returned as a map instead:</li>
  <li>The header option can also just be a list of columns:</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitfasta"></a>[OP] splitFasta

<table>
  <tr><td>
<strong>[OP] splitFasta</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- splitFasta

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The splitFasta operator splits FASTA files or text from a source channel into individual sequences.</li>
  <li>The by option can be used to group sequences into chunks of a given size.</li>
  <li>The following example shows how to read a FASTA file and split it into chunks of 10 sequences each:</li>
  <li>The record option can be used to split FASTA content into records instead of text chunks.</li>
  <li>Each record is a map that allows you to access the FASTA sequence data with ease.</li>
  <li>For example:</li>
  <li>The above example loads the misc/sample.fa file, splits it into records containing the id and seqString fields (i.e.</li>
  <li>the sequence id and the sequence data), filters records by their ID, and finally prints the sequence string of each record.</li>
  <li>Available options:</li>
  <li>See also: countFasta</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitfastq"></a>[OP] splitFastq

<table>
  <tr><td>
<strong>[OP] splitFastq</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- splitFastq

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The splitFastq operator splits FASTQ files or text from a source channel into individual sequences.</li>
  <li>The by option can be used to group sequences into chunks of a given size.</li>
  <li>The following example shows how to read a FASTQ file and split it into chunks of 10 sequences each:</li>
  <li>The record option can be used to split FASTQ content into records instead of text chunks.</li>
  <li>Each record is a map that allows you to access the FASTQ sequence data with ease.</li>
  <li>For example:</li>
  <li>The pe option can be used to split paired-end FASTQ files.</li>
  <li>Available options:</li>
  <li>See also: countFastq</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The source channel must emit tuples containing the file pairs.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splitjson"></a>[OP] splitJson

<table>
  <tr><td>
<strong>[OP] splitJson</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- splitJson

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The splitJson operator splits JSON files or text from a source channel into individual records.</li>
  <li>If the source item is a JSON array, each element of the array will be emitted:</li>
  <li>If the source item is a JSON object, each key-value pair will be emitted as a map with the properties key and value :</li>
  <li>The path option can be used to query a section of the JSON document to parse and split:</li>
  <li>Available options:</li>
  <li>See also: countJson</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-splittext"></a>[OP] splitText

<table>
  <tr><td>
<strong>[OP] splitText</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- splitText

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The splitText operator splits multi-line text content from a source channel into chunks of N lines:</li>
  <li>The above example loads a collection of text files, splits the content of each file into individual lines, and prints each line.</li>
  <li>The by option can be used to emit chunks of N lines:</li>
  <li>An optional closure can be used to transform each text chunk produced by the operator.</li>
  <li>The following example shows how to split text files into chunks of 10 lines and transform them to uppercase letters:</li>
  <li>Available options:</li>
  <li>See also: countLines</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-subscribe"></a>[OP] subscribe

<table>
  <tr><td>
<strong>[OP] subscribe</strong><br/>
Returns: nothing<br/>
  </td></tr>
</table>

**At a glance:** Returns: nothing

#### Related Terms
- subscribe

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: nothing</li>
  <li>The subscribe operator invokes a custom function for each item from a source channel:</li>
  <li>The subscribe operator supports multiple types of event handlers:</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-sum"></a>[OP] sum

<table>
  <tr><td>
<strong>[OP] sum</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- sum

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The sum operator emits the sum of all items in a source channel:</li>
  <li>An optional closure can be used to transform each item before it is added to the sum:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-take"></a>[OP] take

<table>
  <tr><td>
<strong>[OP] take</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- take

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The take operator takes the first N items from a source channel:</li>
  <li>See also: until</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tap"></a>[OP] tap

<table>
  <tr><td>
<strong>[OP] tap</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- tap

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The tap operator assigns a source channel to a variable, and emits the source channel.</li>
  <li>It is a useful way to extract intermediate output channels from a chain of operators.</li>
  <li>For example:</li>
  <li>See also: set</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tointeger"></a>[OP] toInteger

<table>
  <tr><td>
<strong>[OP] toInteger</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- toInteger

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The toInteger operator converts string values from a source channel to integer values:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tolist"></a>[OP] toList

<table>
  <tr><td>
<strong>[OP] toList</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- toList

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The toList operator collects all the items from a source channel into a list and emits the list as a single item:</li>
  <li>See also: collect</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-tosortedlist"></a>[OP] toSortedList

<table>
  <tr><td>
<strong>[OP] toSortedList</strong><br/>
Returns: dataflow value<br/>
  </td></tr>
</table>

**At a glance:** Returns: dataflow value

#### Related Terms
- toSortedList

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: dataflow value</li>
  <li>The toSortedList operator collects all the items from a source channel into a sorted list and emits the list as a single item:</li>
  <li>An optional closure can be used to control how items are compared when sorting.</li>
  <li>For example, to sort tuples by their second element in descending order:</li>
  <li>See also: collect</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-transpose"></a>[OP] transpose

<table>
  <tr><td>
<strong>[OP] transpose</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- transpose

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The transpose operator atransposesa each tuple from a source channel by flattening any nested list in each tuple, emitting each nested item separately.</li>
  <li>To be more precise, the operator transforms a sequence of tuples like (K, list(V), list(W), ..) into a sequence of tuples like (K, V, W, ..) .</li>
  <li>For example:</li>
  <li>The remainder option can be used to emit any incomplete items:</li>
  <li>Available options:</li>
  <li>See also: groupTuple</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>If each source item has more than two elements, these will be flattened by the first element in the item, and a new item will be emitted only when it is complete:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-unique"></a>[OP] unique

<table>
  <tr><td>
<strong>[OP] unique</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- unique

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The unique operator emits the unique items from a source channel:</li>
  <li>An optional closure can be used to transform each item before it is evaluated for uniqueness:</li>
  <li>See also: distinct</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-until"></a>[OP] until

<table>
  <tr><td>
<strong>[OP] until</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- until

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The until operator emits each item from a source channel until a stopping condition is satisfied:</li>
  <li>See also: take</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="operator-view"></a>[OP] view

<table>
  <tr><td>
<strong>[OP] view</strong><br/>
Returns: channel<br/>
  </td></tr>
</table>

**At a glance:** Returns: channel

#### Related Terms
- view

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Returns: channel</li>
  <li>The view operator prints each item from a source channel to standard output:</li>
  <li>An optional closure can be used to transform each item before it is printed:</li>
  <li>The view operator also emits every item that it receives, allowing it to be chained with other operators.</li>
  <li>Available options:</li>
  <li>View a projectas script file(s).</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The view command is used to inspect the pipelines that are already stored in the global nextflow cache.</li>
  <li>For downloading a pipeline into the global cache ~/.nextflow/assets , refer to the pull command.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Viewing the contents of a downloaded pipeline.</li>
  <li>List the folder structure of the downloaded pipeline:</li>
  <li>View the contents of a downloaded pipeline without omitting the header:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [CLI] CLI

### <a id="cli-config"></a>[CLI] Config

<table>
  <tr><td>
<strong>[CLI] Config</strong><br/>
Print the resolved pipeline configuration.<br/>
  </td></tr>
</table>

**At a glance:** Print the resolved pipeline configuration.

#### Related Terms
- config
- Executor-specific configuration

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Print the resolved pipeline configuration.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The config command is used for printing the projectas configuration i.e.</li>
  <li>the nextflow.config and is especially useful for understanding the resolved profiles and parameters that Nextflow will use run a pipeline.</li>
  <li>For in-depth information, please refer the Config profiles section.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Print out the inferred config using a the default group key-value notation.</li>
  <li>Print out the config using a flat notation.</li>
  <li>Print out the config using the Java properties notation.</li>
  <li>Print out the value of a specific configuration property.</li>
  <li>Print out all profiles from the projectas configuration.</li>
  <li>Executor config settings can be applied to specific executors by prefixing the executor name with the symbol $ and using it as special scope.</li>
  <li>For example:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-auth"></a>[CLI] auth

<table>
  <tr><td>
<strong>[CLI] auth</strong><br/>
Manage Seqera Platform authentication.<br/>
  </td></tr>
</table>

**At a glance:** Manage Seqera Platform authentication.

#### Related Terms
- auth

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Manage Seqera Platform authentication.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The auth command provides authentication and configuration management for Seqera.</li>
  <li>For Seqera Cloud, it uses an OAuth2 authentication flow to generate and save a Personal Access Token (PAT) locally.</li>
  <li>For Seqera Enterprise installations, it uses direct PAT authentication.</li>
  <li>Credentials are saved to ~/.nextflow/seqera-auth.config .</li>
  <li>An includeConfig statement is automatically added to ~/.nextflow/config or the configuration file set using $NXF_HOME .</li>
  <li>Options</li>
  <li>Subcommands</li>
  <li>Examples</li>
  <li>Authenticate with Seqera Cloud:</li>
  <li>Authenticate with an Enterprise installation:</li>
  <li>View current authentication status:</li>
  <li>Configure Seqera settings:</li>
  <li>Remove authentication:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-clean"></a>[CLI] clean

<table>
  <tr><td>
<strong>[CLI] clean</strong><br/>
Clean up cache and work directories.<br/>
  </td></tr>
</table>

**At a glance:** Clean up cache and work directories.

#### Related Terms
- clean

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Clean up cache and work directories.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>Upon invocation within a directory, nextflow creates a project specific .nextflow.log file, .nextflow cache directory as well as a work directory.</li>
  <li>The clean command is designed to facilitate removal of these files from previous executions.</li>
  <li>A list of run names and session ids can be generated by invoking nextflow log -q .</li>
  <li>If no run name or session id is provided, it will clean the latest run.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Dry run to remove work directories for the run name boring_euler :</li>
  <li>Remove work directories for the run name boring_euler .</li>
  <li>Remove the execution entries except for a specific execution.</li>
  <li>Dry run to remove the execution data before a specific execution.</li>
  <li>Dry run to remove the execution data after a specific execution.</li>
  <li>Dry run to remove the temporary execution data for a specific execution, while keeping the log files.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-clone"></a>[CLI] clone

<table>
  <tr><td>
<strong>[CLI] clone</strong><br/>
Clone a remote project into a folder.<br/>
  </td></tr>
</table>

**At a glance:** Clone a remote project into a folder.

#### Related Terms
- clone

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Clone a remote project into a folder.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The clone command downloads a pipeline from a Git-hosting platform into the current directory and modifies it accordingly.</li>
  <li>For downloading a pipeline into the global cache ~/.nextflow/assets , please refer to the nextflow pull command.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Clone the latest revision of a pipeline.</li>
  <li>Clone a specific revision of a pipeline.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-commands"></a>[CLI] Commands

<table>
  <tr><td>
<strong>[CLI] Commands</strong><br/>
Reference for Commands.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Commands.

#### Related Terms
- Commands

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-console"></a>[CLI] console

<table>
  <tr><td>
<strong>[CLI] console</strong><br/>
Launch the Nextflow interactive console.<br/>
  </td></tr>
</table>

**At a glance:** Launch the Nextflow interactive console.

#### Related Terms
- console

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Launch the Nextflow interactive console.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The console command provides a Graphical User Interface (GUI) and an interactive REPL (Read-Eval-Print-Loop) for quick experimentation.</li>
  <li>Options</li>
  <li>None available</li>
  <li>Examples</li>
  <li>Launch the console GUI.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-drop"></a>[CLI] drop

<table>
  <tr><td>
<strong>[CLI] drop</strong><br/>
Delete the local copy of a project.<br/>
  </td></tr>
</table>

**At a glance:** Delete the local copy of a project.

#### Related Terms
- drop

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Delete the local copy of a project.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The drop command is used to remove the projects which have been downloaded into the global cache.</li>
  <li>Please refer the list command for generating a list of downloaded pipelines.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Drop the nextflow-io/hello project.</li>
  <li>Forcefully drop the nextflow-io/hello pipeline, ignoring any local changes.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-fs"></a>[CLI] fs

<table>
  <tr><td>
<strong>[CLI] fs</strong><br/>
Perform basic filesystem operations.<br/>
  </td></tr>
</table>

**At a glance:** Perform basic filesystem operations.

#### Related Terms
- fs

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Perform basic filesystem operations.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The fs command is used to perform filesystem operations like copy, move, delete, list directory, etc.</li>
  <li>Like the file() method, it can work with local files, remote URLs, and remote object storage.</li>
  <li>Storage credentials can be provided through the same manner as launching a pipeline (Nextflow config, environment vars, etc).</li>
  <li>Options</li>
  <li>Examples</li>
  <li>List a directory.</li>
  <li>Print the contents of a file to standard output.</li>
  <li>Copy a file or directory.</li>
  <li>Move a file or directory.</li>
  <li>Delete a file or directory.</li>
  <li>Print file or directory attributes.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-help"></a>[CLI] help

<table>
  <tr><td>
<strong>[CLI] help</strong><br/>
Print the top-level help or specific help for a command.<br/>
  </td></tr>
</table>

**At a glance:** Print the top-level help or specific help for a command.

#### Related Terms
- help

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Print the top-level help or specific help for a command.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The help command prints out the overview of the CLI interface and enumerates the top-level options and commands .</li>
  <li>Note that this command is equivalent to simply invoking nextflow at the command line.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Invoke the help option for the drop command.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-info"></a>[CLI] info

<table>
  <tr><td>
<strong>[CLI] info</strong><br/>
Print project or system runtime information.<br/>
  </td></tr>
</table>

**At a glance:** Print project or system runtime information.

#### Related Terms
- info

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Print project or system runtime information.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The info command prints out the nextflow runtime information about the hardware as well as the software versions of the Nextflow version and build, operating system, and Groovy and Java runtime.</li>
  <li>It can also be used to display information about a specific project.</li>
  <li>If no run name or session id is provided, it will clean the latest run.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Display Nextflow runtime and system info:</li>
  <li>Display information about a specific project:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-inspect"></a>[CLI] inspect

<table>
  <tr><td>
<strong>[CLI] inspect</strong><br/>
Inspect process settings in a pipeline project.<br/>
  </td></tr>
</table>

**At a glance:** Inspect process settings in a pipeline project.

#### Related Terms
- inspect

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Inspect process settings in a pipeline project.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The inspect command allows you to determine the container for each process in a pipeline without running the pipeline.</li>
  <li>It prints to stdout a listing of containers for each process, formatted either as JSON or Nextflow configuration.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Get the list of containers used by a pipeline.</li>
  <li>Specify parameters as with the run command:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Currently only supports the container directive.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-kuberun"></a>[CLI] kuberun

<table>
  <tr><td>
<strong>[CLI] kuberun</strong><br/>
Launch a Nextflow pipeline on a Kubernetes cluster.<br/>
  </td></tr>
</table>

**At a glance:** Launch a Nextflow pipeline on a Kubernetes cluster.

#### Related Terms
- kuberun

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Launch a Nextflow pipeline on a Kubernetes cluster.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The kuberun command builds upon the run command and offers a deep integration with the Kubernetes execution environment.</li>
  <li>This command deploys the Nextflow runtime as a Kubernetes pod and assumes that you&#x27;ve already installed the kubectl CLI.</li>
  <li>The kuberun command does not allow the execution of local Nextflow scripts.</li>
  <li>See Kubernetes for more information.</li>
  <li>Options</li>
  <li>The kuberun command supports the following options from run :</li>
  <li>The following new options are also available:</li>
  <li>Examples</li>
  <li>Execute a pipeline into a Kubernetes cluster.</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>-cache</li>
  <li>-disable-jobs-cancellation</li>
  <li>-dsl1</li>
  <li>-dsl2</li>
  <li>-dump-channels</li>
  <li>-dump-hashes</li>
  <li>-e.&lt;key&gt;=&lt;value&gt;</li>
  <li>-entry</li>
  <li>-h, -help</li>
  <li>-hub</li>
  <li>-latest</li>
  <li>-main-script</li>
  <li>-name</li>
  <li>-offline</li>
  <li>-params-file</li>
  <li>-plugins</li>
  <li>-preview</li>
  <li>-process.&lt;key&gt;=&lt;value&gt;</li>
  <li>-profile</li>
  <li>-qs, -queue-size</li>
  <li>-resume</li>
  <li>-r, -revision</li>
  <li>-stub, -stub-run</li>
  <li>-user</li>
  <li>-with-conda</li>
  <li>-with-dag</li>
  <li>-N, -with-notification</li>
  <li>-with-report</li>
  <li>-with-spack</li>
  <li>-with-timeline</li>
  <li>-with-tower</li>
  <li>-with-trace</li>
  <li>-with-wave</li>
  <li>-with-weblog</li>
  <li>-without-spack</li>
  <li>-without-wave</li>
  <li>-w, -work-dir</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-launch"></a>[CLI] launch

<table>
  <tr><td>
<strong>[CLI] launch</strong><br/>
Launch a workflow in Seqera Platform .<br/>
  </td></tr>
</table>

**At a glance:** Launch a workflow in Seqera Platform .

#### Related Terms
- launch

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Launch a workflow in Seqera Platform .</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The launch command launches a pipeline run in Seqera Platform.</li>
  <li>To log in and configure the execution environment, use the auth command.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Execute a pipeline in Seqera Platform.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-lineage"></a>[CLI] lineage

<table>
  <tr><td>
<strong>[CLI] lineage</strong><br/>
Inspect lineage metadata for Nextflow runs.<br/>
  </td></tr>
</table>

**At a glance:** Inspect lineage metadata for Nextflow runs.

#### Related Terms
- lineage

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Inspect lineage metadata for Nextflow runs.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The lineage command is used to inspect lineage metadata.</li>
  <li>See the Getting started with data lineage guide to learn how to get started with data lineage.</li>
  <li>Options</li>
  <li>Subcommands</li>
  <li>The lineage scope controls the generation of lineage metadata.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-lint"></a>[CLI] lint

<table>
  <tr><td>
<strong>[CLI] lint</strong><br/>
Lint Nextflow scripts and config files.<br/>
  </td></tr>
</table>

**At a glance:** Lint Nextflow scripts and config files.

#### Related Terms
- lint

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Lint Nextflow scripts and config files.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The lint command parses and analyzes the given Nextflow scripts and config files, formats them if specified, and prints any errors.</li>
  <li>Directories are recursively scanned for scripts and config files to lint.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Lint a specific file.</li>
  <li>Lint all files in the current directory (and subdirectories) with concise output.</li>
  <li>Lint and format all files in the current directory (and subdirectories) and use two spaces per indent.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-list"></a>[CLI] list

<table>
  <tr><td>
<strong>[CLI] list</strong><br/>
List all downloaded projects.<br/>
  </td></tr>
</table>

**At a glance:** List all downloaded projects.

#### Related Terms
- list

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>List all downloaded projects.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The list commands prints a list of the projects which are already downloaded into the global cache ~/.nextflow/assets .</li>
  <li>Options</li>
  <li>Examples</li>
  <li>List the downloaded pipelines.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-log"></a>[CLI] log

<table>
  <tr><td>
<strong>[CLI] log</strong><br/>
Print the execution history and log information.<br/>
  </td></tr>
</table>

**At a glance:** Print the execution history and log information.

#### Related Terms
- log

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Print the execution history and log information.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The log command is used to query the execution metadata associated with pipelines executed by Nextflow.</li>
  <li>The list of executed pipelines can be generated by running nextflow log .</li>
  <li>Instead of run name, it&#x27;s also possible to use a session id.</li>
  <li>Moreover, this command contains multiple options to facilitate the queries and is especially useful while debugging a pipeline and while inspecting pipeline execution metadata.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Listing the execution logs of previous invocations of all pipelines in a project.</li>
  <li>List the execution entries after a specific execution.</li>
  <li>List the execution entries before a specific execution.</li>
  <li>List the execution entries except for a specific execution.</li>
  <li>Filter specific fields from the execution log of a process.</li>
  <li>Filter fields from the execution log of a process based on a criteria.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Listing only the run names of the execution logs of all pipelines invocations in a project.</li>
  <li>List the execution entries only a specific execution.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-options"></a>[CLI] Options

<table>
  <tr><td>
<strong>[CLI] Options</strong><br/>
The top-level options are meant to be invoked in relation to the core Nextflow
application and are applied to all commands.<br/>
  </td></tr>
</table>

**At a glance:** The top-level options are meant to be invoked in relation to
the core Nextflow application and are applied to all commands.

#### Related Terms
- Options

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The top-level options are meant to be invoked in relation to the core Nextflow application and are applied to all commands.</li>
  <li>For options specific to any command, refer the CLI Commands section.</li>
  <li>Available options:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-plugin"></a>[CLI] plugin

<table>
  <tr><td>
<strong>[CLI] plugin</strong><br/>
Manage plugins and run plugin-specific commands.<br/>
  </td></tr>
</table>

**At a glance:** Manage plugins and run plugin-specific commands.

#### Related Terms
- plugin

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Manage plugins and run plugin-specific commands.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-pull"></a>[CLI] pull

<table>
  <tr><td>
<strong>[CLI] pull</strong><br/>
Download or update a project.<br/>
  </td></tr>
</table>

**At a glance:** Download or update a project.

#### Related Terms
- pull

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Download or update a project.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The pull command downloads a pipeline from a Git-hosting platform into the global cache ~/.nextflow/assets and modifies it accordingly.</li>
  <li>For downloading a pipeline into a local directory, please refer to the nextflow clone command.</li>
  <li>Options</li>
  <li>Examples</li>
  <li>Download a new pipeline or pull the latest revision for a specific project.</li>
  <li>Pull the latest revision for all downloaded projects.</li>
  <li>Download a specific revision of a new project or pull the latest revision for a specific project.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-run"></a>[CLI] run

<table>
  <tr><td>
<strong>[CLI] run</strong><br/>
Execute a pipeline.<br/>
  </td></tr>
</table>

**At a glance:** Execute a pipeline.

#### Related Terms
- run

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Execute a pipeline.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The run command is used to execute a local pipeline script or remote pipeline project.</li>
  <li>Options</li>
  <li>Examples</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Run a specific revision of a remote pipeline. $ nextflow run nextflow-io/hello -r v1.1 N E X T F L O W ~ version 20.07.1 Launching `nextflow-io/hello` [grave_cajal] - revision: 1c3e9e7404 [v1.1]</li>
  <li>Choose a profile for running the project. Assumes that a profile named docker has already been defined in the config file. $ nextflow run main.nf -profile docker</li>
  <li>Execute a pipeline and generate the summary HTML report. For more information on the metrics, please refer the Reports section: $ nextflow run main.nf -with-report</li>
  <li>Execute a pipeline with a custom queue size. By default, the queue size is the number of available CPUs. $ nextflow run nextflow-io/hello -qs 4</li>
  <li>Invoke the pipeline with a specific workflow as the entry-point. $ nextflow run main.nf -entry workflow_A</li>
  <li>Execute a pipeline with integrated monitoring in Seqera Platform . $ nextflow run nextflow-io/hello -with-tower</li>
  <li>Execute a pipeline with a custom parameters file (YAML or JSON). $ nextflow run main.nf -params-file pipeline_params.yml See Pipeline parameters for more information about writing custom parameters files.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-secrets"></a>[CLI] secrets

<table>
  <tr><td>
<strong>[CLI] secrets</strong><br/>
Manage pipeline secrets .<br/>
  </td></tr>
</table>

**At a glance:** Manage pipeline secrets .

#### Related Terms
- secrets

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Manage pipeline secrets .</li>
  <li>Usage</li>
  <li>Options</li>
  <li>Subcommands</li>
  <li>Examples</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Set a secret: $ nextflow secrets set FOO &quot;Hello world&quot;</li>
  <li>List secrets: $ nextflow secrets list</li>
  <li>Get a secret: $ nextflow secrets get FOO</li>
  <li>Delete a secret: $ nextflow secrets delete FOO</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="cli-self-update"></a>[CLI] self-update

<table>
  <tr><td>
<strong>[CLI] self-update</strong><br/>
Update the nextflow runtime to the latest available version.<br/>
  </td></tr>
</table>

**At a glance:** Update the nextflow runtime to the latest available version.

#### Related Terms
- self-update

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Update the nextflow runtime to the latest available version.</li>
  <li>Usage</li>
  <li>Description</li>
  <li>The self-update command directs the nextflow CLI to update itself to the latest stable release.</li>
  <li>Examples</li>
  <li>Update Nextflow.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [CFG] Config

### <a id="config-apptainer"></a>[CFG] apptainer

<table>
  <tr><td>
<strong>[CFG] apptainer</strong><br/>
The apptainer scope controls how Apptainer containers are executed by
Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The apptainer scope controls how Apptainer containers are
executed by Nextflow.

#### Related Terms
- apptainer

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The apptainer scope controls how Apptainer containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-aws"></a>[CFG] aws

<table>
  <tr><td>
<strong>[CFG] aws</strong><br/>
The aws scope controls the interactions with AWS, including AWS Batch and
S3.<br/>
  </td></tr>
</table>

**At a glance:** The aws scope controls the interactions with AWS, including AWS
Batch and S3.

#### Related Terms
- aws

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The aws scope controls the interactions with AWS, including AWS Batch and S3.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-azure"></a>[CFG] azure

<table>
  <tr><td>
<strong>[CFG] azure</strong><br/>
The azure scope allows you to configure the interactions with Azure, including
Azure Batch and Azure Blob Storage.<br/>
  </td></tr>
</table>

**At a glance:** The azure scope allows you to configure the interactions with
Azure, including Azure Batch and Azure Blob Storage.

#### Related Terms
- azure

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The azure scope allows you to configure the interactions with Azure, including Azure Batch and Azure Blob Storage.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-charliecloud"></a>[CFG] charliecloud

<table>
  <tr><td>
<strong>[CFG] charliecloud</strong><br/>
The charliecloud scope controls how Charliecloud containers are executed by
Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The charliecloud scope controls how Charliecloud containers are
executed by Nextflow.

#### Related Terms
- charliecloud

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The charliecloud scope controls how Charliecloud containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-dag"></a>[CFG] dag

<table>
  <tr><td>
<strong>[CFG] dag</strong><br/>
The dag scope controls the workflow diagram generated by Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The dag scope controls the workflow diagram generated by
Nextflow.

#### Related Terms
- dag

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The dag scope controls the workflow diagram generated by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-docker"></a>[CFG] docker

<table>
  <tr><td>
<strong>[CFG] docker</strong><br/>
The docker scope controls how Docker containers are executed by Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The docker scope controls how Docker containers are executed by
Nextflow.

#### Related Terms
- docker

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The docker scope controls how Docker containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-env"></a>[CFG] env

<table>
  <tr><td>
<strong>[CFG] env</strong><br/>
The env scope allows the definition one or more variables that will be exported
into the environment where workflow tasks are executed.<br/>
  </td></tr>
</table>

**At a glance:** The env scope allows the definition one or more variables that
will be exported into the environment where workflow tasks are executed.

#### Related Terms
- env

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The env scope allows the definition one or more variables that will be exported into the environment where workflow tasks are executed.</li>
  <li>Simply prefix your variable names with the env scope or surround them by curly brackets, as shown below:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-executor-specific-defaults"></a>[CFG] Executor-specific defaults

<table>
  <tr><td>
<strong>[CFG] Executor-specific defaults</strong><br/>
Some executor settings have different default values depending on the
executor.<br/>
  </td></tr>
</table>

**At a glance:** Some executor settings have different default values depending
on the executor.

#### Related Terms
- Executor-specific defaults

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Some executor settings have different default values depending on the executor.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-fusion"></a>[CFG] fusion

<table>
  <tr><td>
<strong>[CFG] fusion</strong><br/>
The fusion scope provides advanced configuration for the use of the Fusion file
system .<br/>
  </td></tr>
</table>

**At a glance:** The fusion scope provides advanced configuration for the use of
the Fusion file system .

#### Related Terms
- fusion

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The fusion scope provides advanced configuration for the use of the Fusion file system .</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-google"></a>[CFG] google

<table>
  <tr><td>
<strong>[CFG] google</strong><br/>
The google scope allows you to configure the interactions with Google Cloud,
including Google Cloud Batch and Google Cloud Storage.<br/>
  </td></tr>
</table>

**At a glance:** The google scope allows you to configure the interactions with
Google Cloud, including Google Cloud Batch and Google Cloud Storage.

#### Related Terms
- google

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The google scope allows you to configure the interactions with Google Cloud, including Google Cloud Batch and Google Cloud Storage.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-java-settings"></a>[CFG] Java settings

<table>
  <tr><td>
<strong>[CFG] Java settings</strong><br/>
Reference for Java settings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Java settings.

#### Related Terms
- Java settings

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-k8s"></a>[CFG] k8s

<table>
  <tr><td>
<strong>[CFG] k8s</strong><br/>
The k8s scope controls the deployment and execution of workflow applications in
a Kubernetes cluster.<br/>
  </td></tr>
</table>

**At a glance:** The k8s scope controls the deployment and execution of workflow
applications in a Kubernetes cluster.

#### Related Terms
- k8s

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The k8s scope controls the deployment and execution of workflow applications in a Kubernetes cluster.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-mail"></a>[CFG] mail

<table>
  <tr><td>
<strong>[CFG] mail</strong><br/>
The mail scope controls the mail server used to send email notifications.<br/>
  </td></tr>
</table>

**At a glance:** The mail scope controls the mail server used to send email
notifications.

#### Related Terms
- mail

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The mail scope controls the mail server used to send email notifications.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-manifest"></a>[CFG] manifest

<table>
  <tr><td>
<strong>[CFG] manifest</strong><br/>
The manifest scope allows you to define some metadata that is useful when
publishing or running your pipeline.<br/>
  </td></tr>
</table>

**At a glance:** The manifest scope allows you to define some metadata that is
useful when publishing or running your pipeline.

#### Related Terms
- manifest

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The manifest scope allows you to define some metadata that is useful when publishing or running your pipeline.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-nextflow"></a>[CFG] nextflow

<table>
  <tr><td>
<strong>[CFG] nextflow</strong><br/>
Reference for nextflow.<br/>
  </td></tr>
</table>

**At a glance:** Reference for nextflow.

#### Related Terms
- nextflow

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-nextflow-settings"></a>[CFG] Nextflow settings

<table>
  <tr><td>
<strong>[CFG] Nextflow settings</strong><br/>
Reference for Nextflow settings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Nextflow settings.

#### Related Terms
- Nextflow settings

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-notification"></a>[CFG] notification

<table>
  <tr><td>
<strong>[CFG] notification</strong><br/>
The notification scope controls the automatic sending of an email notification
on workflow completion.<br/>
  </td></tr>
</table>

**At a glance:** The notification scope controls the automatic sending of an
email notification on workflow completion.

#### Related Terms
- notification

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The notification scope controls the automatic sending of an email notification on workflow completion.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-other-settings"></a>[CFG] Other settings

<table>
  <tr><td>
<strong>[CFG] Other settings</strong><br/>
Reference for Other settings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Other settings.

#### Related Terms
- Other settings

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-podman"></a>[CFG] podman

<table>
  <tr><td>
<strong>[CFG] podman</strong><br/>
The podman scope controls how Podman containers are executed by Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The podman scope controls how Podman containers are executed by
Nextflow.

#### Related Terms
- podman

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The podman scope controls how Podman containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-report"></a>[CFG] report

<table>
  <tr><td>
<strong>[CFG] report</strong><br/>
The report scope allows you to configure the workflow Execution report .<br/>
  </td></tr>
</table>

**At a glance:** The report scope allows you to configure the workflow Execution
report .

#### Related Terms
- report

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The report scope allows you to configure the workflow Execution report .</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-sarus"></a>[CFG] sarus

<table>
  <tr><td>
<strong>[CFG] sarus</strong><br/>
The sarus scope controls how Sarus containers are executed by Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The sarus scope controls how Sarus containers are executed by
Nextflow.

#### Related Terms
- sarus

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The sarus scope controls how Sarus containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-seqera-platform-settings"></a>[CFG] Seqera Platform settings

<table>
  <tr><td>
<strong>[CFG] Seqera Platform settings</strong><br/>
Reference for Seqera Platform settings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Seqera Platform settings.

#### Related Terms
- Seqera Platform settings

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-shifter"></a>[CFG] shifter

<table>
  <tr><td>
<strong>[CFG] shifter</strong><br/>
The shifter scope controls how Shifter containers are executed by Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The shifter scope controls how Shifter containers are executed
by Nextflow.

#### Related Terms
- shifter

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The shifter scope controls how Shifter containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-singularity"></a>[CFG] singularity

<table>
  <tr><td>
<strong>[CFG] singularity</strong><br/>
The singularity scope controls how Singularity containers are executed by
Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The singularity scope controls how Singularity containers are
executed by Nextflow.

#### Related Terms
- singularity

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The singularity scope controls how Singularity containers are executed by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-timeline"></a>[CFG] timeline

<table>
  <tr><td>
<strong>[CFG] timeline</strong><br/>
The timeline scope controls the execution timeline report generated by
Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The timeline scope controls the execution timeline report
generated by Nextflow.

#### Related Terms
- timeline

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The timeline scope controls the execution timeline report generated by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-tower"></a>[CFG] tower

<table>
  <tr><td>
<strong>[CFG] tower</strong><br/>
The tower scope controls the settings for Seqera Platform (formerly Tower
Cloud).<br/>
  </td></tr>
</table>

**At a glance:** The tower scope controls the settings for Seqera Platform
(formerly Tower Cloud).

#### Related Terms
- tower

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The tower scope controls the settings for Seqera Platform (formerly Tower Cloud).</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-trace"></a>[CFG] trace

<table>
  <tr><td>
<strong>[CFG] trace</strong><br/>
The trace scope controls the layout of the execution trace file generated by
Nextflow.<br/>
  </td></tr>
</table>

**At a glance:** The trace scope controls the layout of the execution trace file
generated by Nextflow.

#### Related Terms
- trace

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The trace scope controls the layout of the execution trace file generated by Nextflow.</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-unscoped-options"></a>[CFG] Unscoped options

<table>
  <tr><td>
<strong>[CFG] Unscoped options</strong><br/>
Reference for Unscoped options.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Unscoped options.

#### Related Terms
- Unscoped options

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="config-wave"></a>[CFG] wave

<table>
  <tr><td>
<strong>[CFG] wave</strong><br/>
The wave scope provides advanced configuration for the use of Wave containers
.<br/>
  </td></tr>
</table>

**At a glance:** The wave scope provides advanced configuration for the use of
Wave containers .

#### Related Terms
- wave

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The wave scope provides advanced configuration for the use of Wave containers .</li>
  <li>The following settings are available:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [TY] Types

### <a id="types-channel"></a>[TY] Channel

<table>
  <tr><td>
<strong>[TY] Channel</strong><br/>
A channel (also known as a dataflow channel or queue channel ) is an
asynchronous sequence of values of type E .<br/>
  </td></tr>
</table>

**At a glance:** A channel (also known as a dataflow channel or queue channel )
is an asynchronous sequence of values of type E .

#### Related Terms
- Channel

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of values of type E .</li>
  <li>It is used to facilitate dataflow logic in a workflow.</li>
  <li>See Dataflow for an overview of dataflow types.</li>
  <li>See Operators for the available methods for channels.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-bag"></a>[TY] Bag

<table>
  <tr><td>
<strong>[TY] Bag</strong><br/>
Implements the Iterable trait.<br/>
  </td></tr>
</table>

**At a glance:** Implements the Iterable trait.

#### Related Terms
- Bag

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Implements the Iterable&lt;E&gt; trait.</li>
  <li>A bag is an unordered collection of values of type E .</li>
  <li>The following operations are supported for bags:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-boolean"></a>[TY] Boolean

<table>
  <tr><td>
<strong>[TY] Boolean</strong><br/>
Reference for Boolean.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Boolean.

#### Related Terms
- Boolean

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A boolean literal can be true or false :</li>
  <li>A boolean can be true or false .</li>
  <li>The following operations are supported for booleans:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>&amp;&amp; : logical AND</li>
  <li>|| : logical OR</li>
  <li>! : logical NOT</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-duration"></a>[TY] Duration

<table>
  <tr><td>
<strong>[TY] Duration</strong><br/>
A Duration represents a duration of time with millisecond precision.<br/>
  </td></tr>
</table>

**At a glance:** A Duration represents a duration of time with millisecond
precision.

#### Related Terms
- Duration

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A Duration represents a duration of time with millisecond precision.</li>
  <li>A Duration can be created by adding a unit suffix to an integer (e.g.</li>
  <li>1.h ), or by explicitly casting to Duration :</li>
  <li>The following suffixes are available:</li>
  <li>Durations can be compared like numbers, and they support basic arithmetic operations:</li>
  <li>The following methods are available for a Duration:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-float"></a>[TY] Float

<table>
  <tr><td>
<strong>[TY] Float</strong><br/>
A float is a floating-point number (i.e.<br/>
  </td></tr>
</table>

**At a glance:** A float is a floating-point number (i.e.

#### Related Terms
- Float

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A float is a floating-point number (i.e.</li>
  <li>real number) that can be positive or negative.</li>
  <li>The following operations are supported for floats:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>+, -, *, / : addition, subtraction, multiplication, division</li>
  <li>** : exponentation</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-integer"></a>[TY] Integer

<table>
  <tr><td>
<strong>[TY] Integer</strong><br/>
An integer is a whole number that can be positive or negative.<br/>
  </td></tr>
</table>

**At a glance:** An integer is a whole number that can be positive or negative.

#### Related Terms
- Integer

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An integer is a whole number that can be positive or negative.</li>
  <li>The following operations are supported for integers:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>+, -, *, / : addition, subtraction, multiplication, integer division</li>
  <li>% : remainder of integer division (i.e. modulus)</li>
  <li>** : exponentation</li>
  <li>&amp; , | , ^ , ~ : bitwise AND, OR, XOR, NOT</li>
  <li>&lt;&lt; , &gt;&gt; : left and right bit-shift</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-iterable"></a>[TY] Iterable

<table>
  <tr><td>
<strong>[TY] Iterable</strong><br/>
Implemented by the following types: Bag , List , Set<br/>
  </td></tr>
</table>

**At a glance:** Implemented by the following types: Bag , List , Set

#### Related Terms
- Iterable

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Implemented by the following types: Bag&lt;E&gt; , List&lt;E&gt; , Set&lt;E&gt;</li>
  <li>Iterable is a trait implemented by collection types that support iteration.</li>
  <li>Types that implement Iterable can be passed as an Iterable parameter of a method, and they can use all of the methods described below.</li>
  <li>The following methods are available for iterables:</li>
  <li>toUnique( comparator: (E) -&gt; R ) -&gt; Iterable&lt;E&gt;</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-list"></a>[TY] List

<table>
  <tr><td>
<strong>[TY] List</strong><br/>
Implements the Iterable trait.<br/>
  </td></tr>
</table>

**At a glance:** Implements the Iterable trait.

#### Related Terms
- List

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Implements the Iterable&lt;E&gt; trait.</li>
  <li>A list is an ordered collection of values of type E .</li>
  <li>See Lists for an overview of lists.</li>
  <li>The following operations are supported for lists:</li>
  <li>The following methods are available for a list:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-map"></a>[TY] Map

<table>
  <tr><td>
<strong>[TY] Map</strong><br/>
A map associates or maps keys of type K to values of type V .<br/>
  </td></tr>
</table>

**At a glance:** A map associates or maps keys of type K to values of type V .

#### Related Terms
- Map

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A map associates or maps keys of type K to values of type V .</li>
  <li>See Maps for an overview of maps.</li>
  <li>The following operations are supported for maps:</li>
  <li>The following methods are available for a map:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Each key can map to at most one value a a map cannot contain duplicate keys.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-memoryunit"></a>[TY] MemoryUnit

<table>
  <tr><td>
<strong>[TY] MemoryUnit</strong><br/>
A MemoryUnit represents a quantity of bytes.<br/>
  </td></tr>
</table>

**At a glance:** A MemoryUnit represents a quantity of bytes.

#### Related Terms
- MemoryUnit

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A MemoryUnit represents a quantity of bytes.</li>
  <li>A MemoryUnit can be created by adding a unit suffix to an integer (e.g.</li>
  <li>1.GB ), or by explicitly casting to MemoryUnit :</li>
  <li>The following suffixes are available:</li>
  <li>Memory units can be compared like numbers, and they support basic arithmetic operations:</li>
  <li>The following methods are available for a MemoryUnit object:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-operations"></a>[TY] Operations

<table>
  <tr><td>
<strong>[TY] Operations</strong><br/>
A Path is a handle for hierarchichal paths such as local files and directories,
HTTP/FTP URLs, and object storage paths (e.g.<br/>
  </td></tr>
</table>

**At a glance:** A Path is a handle for hierarchichal paths such as local files
and directories, HTTP/FTP URLs, and object storage paths (e.g.

#### Related Terms
- Operations

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, and object storage paths (e.g.</li>
  <li>Amazon S3).</li>
  <li>The file() function can be used to get a Path for a given filename or URL:</li>
  <li>The files() function can be used to get a collection of Paths from a glob pattern:</li>
  <li>The following sections describe the methods that are available for paths.</li>
  <li>The following operations are supported for paths:</li>
  <li>The following methods are useful for getting attributes of a path:</li>
  <li>The following methods are available for reading files:</li>
  <li>The following methods are available for writing to files:</li>
  <li>The following methods are available for manipulating files and directories in a filesystem:</li>
  <li>The following methods are available for listing and traversing directories:</li>
  <li>The following methods are available for splitting and counting the records in files:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-set"></a>[TY] Set

<table>
  <tr><td>
<strong>[TY] Set</strong><br/>
Implements the Iterable trait.<br/>
  </td></tr>
</table>

**At a glance:** Implements the Iterable trait.

#### Related Terms
- Set

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Implements the Iterable&lt;E&gt; trait.</li>
  <li>A set can be created from a list using the toSet() method:</li>
  <li>The following operations are supported for sets:</li>
  <li>The following methods are available for a set:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>A set is an unordered collection of values of type E which cannot contain duplicates.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-string"></a>[TY] String

<table>
  <tr><td>
<strong>[TY] String</strong><br/>
Reference for String.<br/>
  </td></tr>
</table>

**At a glance:** Reference for String.

#### Related Terms
- String

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A string literal consists of arbitrary text enclosed by single or double quotes:</li>
  <li>A triple-quoted string can span multiple lines:</li>
  <li>A slashy string is enclosed by slashes instead of quotes:</li>
  <li>A string is an immutable sequence of characters.</li>
  <li>See Strings for an overview of strings.</li>
  <li>The following operations are supported for strings:</li>
  <li>The following methods are available for a string:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-tuple"></a>[TY] Tuple

<table>
  <tr><td>
<strong>[TY] Tuple</strong><br/>
A tuple is a fixed sequence of values, where each value can have its own
type.<br/>
  </td></tr>
</table>

**At a glance:** A tuple is a fixed sequence of values, where each value can
have its own type.

#### Related Terms
- Tuple

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A tuple is a fixed sequence of values, where each value can have its own type.</li>
  <li>Tuples can be created using the tuple function.</li>
  <li>The following operations are supported for tuples:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-value"></a>[TY] Value

<table>
  <tr><td>
<strong>[TY] Value</strong><br/>
A dataflow value (also known as a value channel ) is an asynchronous value of
type V .<br/>
  </td></tr>
</table>

**At a glance:** A dataflow value (also known as a value channel ) is an
asynchronous value of type V .

#### Related Terms
- Value

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A dataflow value (also known as a value channel ) is an asynchronous value of type V .</li>
  <li>It is used to facilitate dataflow logic in a workflow.</li>
  <li>See Dataflow for an overview of dataflow types.</li>
  <li>The following methods are available for a dataflow value:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="types-versionnumber"></a>[TY] VersionNumber

<table>
  <tr><td>
<strong>[TY] VersionNumber</strong><br/>
A VersionNumber represents a semantic or calendar version number.<br/>
  </td></tr>
</table>

**At a glance:** A VersionNumber represents a semantic or calendar version
number.

#### Related Terms
- VersionNumber

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A VersionNumber represents a semantic or calendar version number.</li>
  <li>The following methods are available for a VersionNumber:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [SC] Script Language

### <a id="script-language-process"></a>[SC] Process

<table>
  <tr><td>
<strong>[SC] Process</strong><br/>
A process consists of a name and a body.<br/>
  </td></tr>
</table>

**At a glance:** A process consists of a name and a body.

#### Related Terms
- Process
- Process (typed)

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A process consists of a name and a body.</li>
  <li>The process body consists of one or more statements .</li>
  <li>A process may define additional sections for directives , inputs , outputs , script , exec , and stub :</li>
  <li>Each section may contain one or more statements.</li>
  <li>See Process reference for the set of available input qualifiers, output qualifiers, and directives.</li>
  <li>The script section can be substituted with an exec section:</li>
  <li>See Processes for more information on the semantics of each process section.</li>
  <li>A typed process is a process that uses static types for inputs and/or outputs:</li>
  <li>Typed processes may specify the following sections:</li>
  <li>See Processes (typed) for more information on the semantics of typed processes.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>A minimal process definition must return a string:</li>
  <li>For directives, inputs, and outputs, these statements must be function calls .</li>
  <li>The script and stub sections must return a string in the same manner as a function .</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>A process must define a script or exec section (see below). All other sections are optional. Directives do not have an explicit section label, but must be defined first.</li>
  <li>The script: section label can be omitted only when there are no other sections in the body.</li>
  <li>Sections must be defined in the order shown above, with the exception of the output section, which can also be specified after the script and stub.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-function"></a>[SC] Function

<table>
  <tr><td>
<strong>[SC] Function</strong><br/>
Reference for Function.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Function.

#### Related Terms
- Function
- Function call

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A function consists of a name, parameter list, and a body:</li>
  <li>The function body consists of one or more statements .</li>
  <li>The last statement is implicitly treated as a return statement if it is an expression statement that returns a value.</li>
  <li>The return statement can be used to explicitly return from a function:</li>
  <li>A function call consists of a name and argument list:</li>
  <li>A method call consists of an object expression and a function call separated by a dot , spread dot , or safe dot :</li>
  <li>The argument list may contain any number of positional arguments and named arguments :</li>
  <li>The named arguments are collected into a map and provided as the first positional argument to the function.</li>
  <li>The above function call can be rewritten as:</li>
  <li>The parentheses can be omitted when the function call is also an expression statement and there is at least one argument:</li>
  <li>If the last argument is a closure, it can be specified outside of the parentheses:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The argument name must be an identifier or string literal.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-enum"></a>[SC] Enum

<table>
  <tr><td>
<strong>[SC] Enum</strong><br/>
An enum type declaration consists of a name and a body.<br/>
  </td></tr>
</table>

**At a glance:** An enum type declaration consists of a name and a body.

#### Related Terms
- Enum type

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An enum type declaration consists of a name and a body.</li>
  <li>The body consists of a comma-separated list of identifiers:</li>
  <li>Enum values in the above example can be accessed as Day.MONDAY , Day.TUESDAY , and so on.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-variable"></a>[SC] Variable

<table>
  <tr><td>
<strong>[SC] Variable</strong><br/>
Reference for Variable declaration.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Variable declaration.

#### Related Terms
- Variable declaration
- Variable

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Variables can be declared with the def keyword:</li>
  <li>Multiple variables can be declared in a single statement if the initializer is a list literal with the same number of elements and declared variables:</li>
  <li>Each variable has a scope , which is the region of code in which the variable can be used.</li>
  <li>Variables declared in a function, as well as the parameters of that function, exist for the duration of that function call.</li>
  <li>The same applies to closures.</li>
  <li>Workflow inputs exist for the entire workflow body.</li>
  <li>Variables declared in the main section exist for the main, emit, and publish sections.</li>
  <li>Named outputs are not considered variable declarations and therefore do not have any scope.</li>
  <li>Process input variables exist for the entire process body.</li>
  <li>A variable expression is a reference to a variable or other named value:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Variables declared in the process script, exec, and stub sections exist only in their respective section, with one exception a variables declared without the def keyword also exist in the output section.</li>
  <li>Variables declared in an if or else branch exist only within that branch:</li>
  <li>A variable cannot be declared with the same name as another variable in the same scope or an enclosing scope:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-assignment"></a>[SC] Assignment

<table>
  <tr><td>
<strong>[SC] Assignment</strong><br/>
Reference for Assignment.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Assignment.

#### Related Terms
- Assignment

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An assignment statement consists of a target expression and a source expression separated by an equals sign:</li>
  <li>The source expression can be any expression.</li>
  <li>Multiple variables can be assigned in a single statement as long as the source expression is a list literal with the same number of elements and assigned variables:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The target expression must be a variable , index , or property expression.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-include"></a>[SC] Include

<table>
  <tr><td>
<strong>[SC] Include</strong><br/>
Reference for Include.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Include.

#### Related Terms
- Include

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An include declaration consists of an include source and one or more include clauses :</li>
  <li>./module.nf ) or a plugin (e.g.</li>
  <li>plugin/nf-hello ).</li>
  <li>In the above example, hallo is included under the alias sayHello .</li>
  <li>Include clauses can be separated by semi-colons or newlines:</li>
  <li>Include clauses can also be specified as separate includes:</li>
  <li>The following definitions can be included:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The include source should be a string literal and should refer to either a local path (e.g.</li>
  <li>Each include clause should specify a name, and may also specify an alias .</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Functions</li>
  <li>Processes</li>
  <li>Named workflows</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-feature-flag"></a>[SC] Feature flag

<table>
  <tr><td>
<strong>[SC] Feature flag</strong><br/>
A feature flag declaration is an assignment.<br/>
  </td></tr>
</table>

**At a glance:** A feature flag declaration is an assignment.

#### Related Terms
- Feature flag

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A feature flag declaration is an assignment.</li>
  <li>number, string, boolean):</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The target should be a valid feature flag and the source should be a literal (i.e.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-shebang"></a>[SC] Shebang

<table>
  <tr><td>
<strong>[SC] Shebang</strong><br/>
Reference for Shebang.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Shebang.

#### Related Terms
- Shebang

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The first line of a script can be a shebang :</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-assert"></a>[SC] assert

<table>
  <tr><td>
<strong>[SC] assert</strong><br/>
Reference for assert.<br/>
  </td></tr>
</table>

**At a glance:** Reference for assert.

#### Related Terms
- assert

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An assert statement consists of the assert keyword followed by a boolean expression, with an optional error message separated by a colon:</li>
  <li>If the condition is false, an error will be raised with the given error message.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-binary-expressions"></a>[SC] Binary expressions

<table>
  <tr><td>
<strong>[SC] Binary expressions</strong><br/>
Reference for Binary expressions.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Binary expressions.

#### Related Terms
- Binary expressions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A binary expression consists of a left expression and a right expression separated by a binary operator :</li>
  <li>The following binary operators are available:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>** : power (i.e. exponentiation)</li>
  <li>* : multiplication</li>
  <li>/ : division</li>
  <li>% : remainder (i.e. modulo)</li>
  <li>+ : addition</li>
  <li>- : subtraction</li>
  <li>&lt;&lt; : left shift</li>
  <li>&gt;&gt; : right shift</li>
  <li>&gt;&gt;&gt; : unsigned right shift</li>
  <li>.. : inclusive range</li>
  <li>..&lt; : right-exclusive range</li>
  <li>as : type cast</li>
  <li>instanceof : type relation</li>
  <li>!instanceof : negated type relation</li>
  <li>&lt; : less than</li>
  <li>&gt; : greater than</li>
  <li>&lt;= : less than or equals</li>
  <li>&gt;= : greater than or equals</li>
  <li>in : membership</li>
  <li>!in : negated membership</li>
  <li>== : equals</li>
  <li>!= : negated equals</li>
  <li>&lt;=&gt; : spaceship (i.e. three-way comparison)</li>
  <li>=~ : regex find</li>
  <li>==~ : regex match</li>
  <li>&amp; : bitwise AND</li>
  <li>^ : bitwise XOR (exclusive or)</li>
  <li>| : bitwise OR</li>
  <li>&amp;&amp; : logical AND</li>
  <li>|| : logical OR</li>
  <li>?: elvis (i.e. short ternary)</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-capturing-groups"></a>[SC] Capturing groups

<table>
  <tr><td>
<strong>[SC] Capturing groups</strong><br/>
You can match a pattern that includes groups.<br/>
  </td></tr>
</table>

**At a glance:** You can match a pattern that includes groups.

#### Related Terms
- Capturing groups

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>You can match a pattern that includes groups.</li>
  <li>First create a matcher object with the =~ operator.</li>
  <li>Then, you can index the matcher object to find the matches: matcher[0] returns a list representing the first match of the regular expression in the string.</li>
  <li>The first list element is the string that matches the entire regular expression, and the remaining elements are the strings that match each group.</li>
  <li>Hereas how it works:</li>
  <li>Applying some syntactic sugar, you can do the same in just one line of code:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-closure"></a>[SC] Closure

<table>
  <tr><td>
<strong>[SC] Closure</strong><br/>
Reference for Closure.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Closure.

#### Related Terms
- Closure

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A closure, also known as an anonymous function, consists of a parameter list followed by zero or more statements, enclosed in curly braces:</li>
  <li>The above closure takes two arguments and returns their sum.</li>
  <li>The closure body is identical to that of a function .</li>
  <li>Closures can access variables outside of their scope:</li>
  <li>See standard library and operator for more examples of how closures are used in practice.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Statements should be separated by newlines or semi-colons, and the last statement is implicitly treated as a return statement :</li>
  <li>Closures can declare local variables that exist only for the lifetime of each closure invocation:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-closures"></a>[SC] Closures

<table>
  <tr><td>
<strong>[SC] Closures</strong><br/>
A closure is a function that can be used like a regular value.<br/>
  </td></tr>
</table>

**At a glance:** A closure is a function that can be used like a regular value.

#### Related Terms
- Closures

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A closure is a function that can be used like a regular value.</li>
  <li>Typically, closures are passed as arguments to higher-order functions to express computations in a declarative manner.</li>
  <li>For example:</li>
  <li>The above example defines a closure, which takes one parameter named v and returns the square of v ( v * v ).</li>
  <li>The closure is assigned to the variable square .</li>
  <li>square can now be called like a function:</li>
  <li>The above example prints 81 .</li>
  <li>The main use case for a closure is as an argument to a higher-order function:</li>
  <li>The collect method of a list applies a mapping function to each value in the list and produces a new list.</li>
  <li>The above example produces:</li>
  <li>The example can be expressed more concisely as:</li>
  <li>Another example is the each method of a map, which takes a closure with two arguments corresponding to the key and value of each map entry:</li>
  <li>Prints:</li>
  <li>Closures can access variables outside of their scope:</li>
  <li>While the each method is a convenient way to iterate through a collection and build up some result, a more idiomatic way to do this is to use the inject method:</li>
  <li>This way, the closure is fully self-contained because it doesn&#x27;t access or mutate any variables outside of its scope.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>A closure can also declare local variables that exist only for the lifetime of each closure invocation:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-comments"></a>[SC] Comments

<table>
  <tr><td>
<strong>[SC] Comments</strong><br/>
A line comment starts with // and includes the rest of the line.<br/>
  </td></tr>
</table>

**At a glance:** A line comment starts with // and includes the rest of the
line.

#### Related Terms
- Comments

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A line comment starts with // and includes the rest of the line.</li>
  <li>A block comment starts with /* and includes all subsequent characters up to the first */ .</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-conditional-execution"></a>[SC] Conditional execution

<table>
  <tr><td>
<strong>[SC] Conditional execution</strong><br/>
One of the most important features of any programming language is the ability to
execute different code under different conditions.<br/>
  </td></tr>
</table>

**At a glance:** One of the most important features of any programming language
is the ability to execute different code under different conditions.

#### Related Terms
- Conditional execution

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>One of the most important features of any programming language is the ability to execute different code under different conditions.</li>
  <li>This can be done with an if-else statement:</li>
  <li>In some cases, conditional statements can be expressed more concisely as a conditional expression (also known as a ternary expression ):</li>
  <li>A shortened version of the conditional expression can be used to return a value if it is truthy, or fallback to a second value otherwise:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-constructor-call"></a>[SC] Constructor call

<table>
  <tr><td>
<strong>[SC] Constructor call</strong><br/>
Reference for Constructor call.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Constructor call.

#### Related Terms
- Constructor call

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A constructor call consists of the new keyword followed by a type name and an argument list enclosed in parentheses:</li>
  <li>If the type is implicitly available in the script, the fully-qualified type name can be elided to the simple type name :</li>
  <li>See Standard library for the set of types that are available in Nextflow scripts.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-deprecations"></a>[SC] Deprecations

<table>
  <tr><td>
<strong>[SC] Deprecations</strong><br/>
Reference for Deprecations.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Deprecations.

#### Related Terms
- Deprecations

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The following legacy features were excluded from this page because they are deprecated:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>The addParams and params clauses of include declarations. See Module parameters for more information.</li>
  <li>The when: section of a process definition. See When for more information.</li>
  <li>The shell: section of a process definition. See Shell for more information.</li>
  <li>The implicit it closure parameter. See Closures for more information.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-dynamic-string"></a>[SC] Dynamic string

<table>
  <tr><td>
<strong>[SC] Dynamic string</strong><br/>
Reference for Dynamic string.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Dynamic string.

#### Related Terms
- Dynamic string

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Double-quoted strings can be interpolated using the ${} placeholder with an expression:</li>
  <li>If the expression is a name or simple property expression (one or more identifiers separated by dots), the curly braces can be omitted:</li>
  <li>Multi-line double-quoted strings can also be interpolated:</li>
  <li>Single-quoted strings are not interpolated:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-expression-statement"></a>[SC] Expression statement

<table>
  <tr><td>
<strong>[SC] Expression statement</strong><br/>
Any expression can be a statement.<br/>
  </td></tr>
</table>

**At a glance:** Any expression can be a statement.

#### Related Terms
- Expression statement

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Any expression can be a statement.</li>
  <li>println ) or an implicit return statement in a function or closure .</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>In general, the only expressions that can have any effect as expression statements are function calls that have side effects (e.g.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-expressions"></a>[SC] Expressions

<table>
  <tr><td>
<strong>[SC] Expressions</strong><br/>
An expression represents a value.<br/>
  </td></tr>
</table>

**At a glance:** An expression represents a value.

#### Related Terms
- Expressions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An expression represents a value.</li>
  <li>A literal value is an expression whose value is known at compile-time, such as a number, string, or boolean.</li>
  <li>Every expression has a type , which may be resolved at compile-time or run-time.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>All other expressions must be evaluated at run-time.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-hello-world"></a>[SC] Hello world

<table>
  <tr><td>
<strong>[SC] Hello world</strong><br/>
Reference for Hello world.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Hello world.

#### Related Terms
- Hello world

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>You can use the println function to print to the console:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-ifelse"></a>[SC] if/else

<table>
  <tr><td>
<strong>[SC] if/else</strong><br/>
An if/else statement consists of an if branch and an optional else branch .<br/>
  </td></tr>
</table>

**At a glance:** An if/else statement consists of an if branch and an optional
else branch .

#### Related Terms
- if/else

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An if/else statement consists of an if branch and an optional else branch .</li>
  <li>Each branch consists of a boolean expression in parentheses, followed by either a single statement or a block statement (one or more statements in curly braces).</li>
  <li>For example:</li>
  <li>If the condition is true, the if branch will be executed, otherwise the else branch will be executed.</li>
  <li>If/else statements can be chained any number of times by making the else branch another if/else statement:</li>
  <li>A more verbose way to write the same code is:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-index-expression"></a>[SC] Index expression

<table>
  <tr><td>
<strong>[SC] Index expression</strong><br/>
Reference for Index expression.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Index expression.

#### Related Terms
- Index expression

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>An index expression consists of a left expression and a right expression , with the right expression enclosed in square brackets:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-list"></a>[SC] List

<table>
  <tr><td>
<strong>[SC] List</strong><br/>
Reference for List.<br/>
  </td></tr>
</table>

**At a glance:** Reference for List.

#### Related Terms
- List

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A list literal consists of a comma-separated list of zero or more expressions, enclosed in square brackets:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-lists"></a>[SC] Lists

<table>
  <tr><td>
<strong>[SC] Lists</strong><br/>
Reference for Lists.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Lists.

#### Related Terms
- Lists

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Lists are defined using square brackets:</li>
  <li>You can access a given item in the list with square-bracket notation (indexes start at 0):</li>
  <li>In order to get the length of the list use the size method:</li>
  <li>See List&lt;E&gt; for the set of available list operations.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-map"></a>[SC] Map

<table>
  <tr><td>
<strong>[SC] Map</strong><br/>
A map literal consists of a comma-separated list of one or more map entries ,
enclosed in square brackets.<br/>
  </td></tr>
</table>

**At a glance:** A map literal consists of a comma-separated list of one or more
map entries , enclosed in square brackets.

#### Related Terms
- Map

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A map literal consists of a comma-separated list of one or more map entries , enclosed in square brackets.</li>
  <li>Each map entry consists of a key expression and value expression separated by a colon:</li>
  <li>An empty map is specified with a single colon to distinguish it from an empty list:</li>
  <li>Both the key and value can be any expression.</li>
  <li>Identifier keys are treated as string literals (i.e.</li>
  <li>the quotes can be omitted).</li>
  <li>A variable can be used as a key by enclosing it in parentheses:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-maps"></a>[SC] Maps

<table>
  <tr><td>
<strong>[SC] Maps</strong><br/>
Maps are used to store associative arrays (also known as dictionaries ).<br/>
  </td></tr>
</table>

**At a glance:** Maps are used to store associative arrays (also known as
dictionaries ).

#### Related Terms
- Maps

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Maps are used to store associative arrays (also known as dictionaries ).</li>
  <li>They are unordered collections of heterogeneous, named data:</li>
  <li>Note that each of the values stored in the map can be of a different type.</li>
  <li>Brett is an integer, Pete is a string, and Andrew is a floating-point number.</li>
  <li>We can access the values in a map in two main ways:</li>
  <li>To add data to or modify a map, the syntax is similar to adding values to list:</li>
  <li>You can also use the + operator to add two maps together:</li>
  <li>When adding two maps, the first map is copied and then appended with the keys from the second map.</li>
  <li>Any conflicting keys are overwritten by the second map.</li>
  <li>See Map&lt;K,V&gt; for the set of available map operations.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-multi-line-strings"></a>[SC] Multi-line strings

<table>
  <tr><td>
<strong>[SC] Multi-line strings</strong><br/>
Reference for Multi-line strings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Multi-line strings.

#### Related Terms
- Multi-line strings

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A block of text that span multiple lines can be defined by delimiting it with triple single or double quotes:</li>
  <li>As in Bash/shell scripts, terminating a line in a multi-line string with a \ character prevents a newline character from separating that line from the one that follows:</li>
  <li>In the preceding example, blastp and its -in , -out , -db and -html switches and their arguments are effectively a single line.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-null"></a>[SC] Null

<table>
  <tr><td>
<strong>[SC] Null</strong><br/>
The null literal is specified as null .<br/>
  </td></tr>
</table>

**At a glance:** The null literal is specified as null .

#### Related Terms
- Null

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The null literal is specified as null .</li>
  <li>It can be used to represent an empty value:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-number"></a>[SC] Number

<table>
  <tr><td>
<strong>[SC] Number</strong><br/>
A number literal can be an integer or floating-point number, and can be positive
or negative.<br/>
  </td></tr>
</table>

**At a glance:** A number literal can be an integer or floating-point number,
and can be positive or negative.

#### Related Terms
- Number

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A number literal can be an integer or floating-point number, and can be positive or negative.</li>
  <li>Integers can specified in binary with 0b , octal with 0 , or hexadecimal with 0x .</li>
  <li>Floating-point numbers can use scientific notation with the e or E prefix.</li>
  <li>Underscores can be used as thousands separators to make long numbers more readable.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-operators"></a>[SC] Operators

<table>
  <tr><td>
<strong>[SC] Operators</strong><br/>
Operators are symbols that perform specific functions on one or more values, and
generally make code easier to read.<br/>
  </td></tr>
</table>

**At a glance:** Operators are symbols that perform specific functions on one or
more values, and generally make code easier to read.

#### Related Terms
- Operators

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Operators are symbols that perform specific functions on one or more values, and generally make code easier to read.</li>
  <li>This section highlights some of the most commonly used operators.</li>
  <li>The == and != operators can be used to test whether any two values are equal (or not equal):</li>
  <li>Comparison operators can be used to compare two values:</li>
  <li>Logical operators can be used to perform Boolean logic:</li>
  <li>The in and !in operators can be used to test membership , i.e.</li>
  <li>whether a collection contains a value:</li>
  <li>Arithmetic operators can be used to do math:</li>
  <li>Some arithmetic operators can be used with other types of values.</li>
  <li>For example, + can be used to concatenate lists, maps, and strings:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-parentheses"></a>[SC] Parentheses

<table>
  <tr><td>
<strong>[SC] Parentheses</strong><br/>
Reference for Parentheses.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Parentheses.

#### Related Terms
- Parentheses

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Any expression can be enclosed in parentheses:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-precedence"></a>[SC] Precedence

<table>
  <tr><td>
<strong>[SC] Precedence</strong><br/>
Reference for Precedence.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Precedence.

#### Related Terms
- Precedence

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Compound expressions are evaluated in the following order:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>parentheses</li>
  <li>property expressions</li>
  <li>function calls</li>
  <li>index expressions</li>
  <li>~ , !</li>
  <li>**</li>
  <li>+ , - (unary)</li>
  <li>* , / , %</li>
  <li>+ , - (binary)</li>
  <li>&lt;&lt; , &gt;&gt;&gt; , &gt;&gt; , .. , ..&lt;</li>
  <li>as</li>
  <li>instanceof , !instanceof</li>
  <li>&lt; , &gt; , &lt;= , &gt;= , in , !in</li>
  <li>== , != , &lt;=&gt;</li>
  <li>=~ , ==~</li>
  <li>&amp;</li>
  <li>^</li>
  <li>|</li>
  <li>&amp;&amp;</li>
  <li>||</li>
  <li>?: (ternary)</li>
  <li>?: (elvis)</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-property-expression"></a>[SC] Property expression

<table>
  <tr><td>
<strong>[SC] Property expression</strong><br/>
Reference for Property expression.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Property expression.

#### Related Terms
- Property expression

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A property expression consists of an object expression and a property , separated by a dot , spread dot , or safe dot :</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>The property must be an identifier or string literal.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-regular-expressions"></a>[SC] Regular expressions

<table>
  <tr><td>
<strong>[SC] Regular expressions</strong><br/>
Regular expressions are the Swiss Army knife of text processing.<br/>
  </td></tr>
</table>

**At a glance:** Regular expressions are the Swiss Army knife of text
processing.

#### Related Terms
- Regular expressions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Regular expressions are the Swiss Army knife of text processing.</li>
  <li>They provide the ability to match and extract patterns from strings.</li>
  <li>Use =~ to check whether a given pattern occurs anywhere in a string:</li>
  <li>Use ==~ to check whether a string matches a given regular expression pattern exactly.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-return"></a>[SC] return

<table>
  <tr><td>
<strong>[SC] return</strong><br/>
Reference for return.<br/>
  </td></tr>
</table>

**At a glance:** Reference for return.

#### Related Terms
- return

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A return statement consists of the return keyword with an optional expression:</li>
  <li>In the case of a nested closure, the return statement will return from the nearest enclosing closure.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Return statements can only be used in functions and closures.</li>
  <li>If a function or closure has multiple return statements (including implicit returns), all of the return statements should either return a value or return nothing.</li>
  <li>If a function or closure does return a value, it should do so for every conditional branch.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-script-declarations"></a>[SC] Script declarations

<table>
  <tr><td>
<strong>[SC] Script declarations</strong><br/>
Reference for Script declarations.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Script declarations.

#### Related Terms
- Script declarations

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A Nextflow script may contain the following top-level declarations:</li>
  <li>Script declarations are in turn composed of statements and expressions.</li>
  <li>If there are no script declarations, a script may contain one or more statements , in which case the entire script is treated as an entry workflow.</li>
  <li>For example:</li>
  <li>Is equivalent to:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Shebang</li>
  <li>Feature flags</li>
  <li>Include declarations</li>
  <li>Params block</li>
  <li>Parameter declarations (legacy)</li>
  <li>Workflow definitions</li>
  <li>Process definitions</li>
  <li>Function definitions</li>
  <li>Enum types</li>
  <li>Output block</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-script-definitions"></a>[SC] Script definitions

<table>
  <tr><td>
<strong>[SC] Script definitions</strong><br/>
So far, we have been focusing on the basic building blocks of Nextflow code,
like variables, lists, strings, and closures.<br/>
  </td></tr>
</table>

**At a glance:** So far, we have been focusing on the basic building blocks of
Nextflow code, like variables, lists, strings, and closures.

#### Related Terms
- Script definitions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>So far, we have been focusing on the basic building blocks of Nextflow code, like variables, lists, strings, and closures.</li>
  <li>In practice, however, Nextflow scripts are composed of workflows , processes , and functions (collectively known as definitions ), and can include definitions from other scripts.</li>
  <li>To transition a code snippet into a proper workflow script, simply wrap it in a workflow block:</li>
  <li>This block is called the entry workflow .</li>
  <li>It serves as the entrypoint when the script is executed.</li>
  <li>You can also break up code into functions, for example:</li>
  <li>See Workflows , Processes , and Modules for more information about how to use these features in your Nextflow scripts.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>A script can only have one entry workflow.</li>
  <li>Whenever a script contains only simple statements like println &#x27;Hello!&#x27; , Nextflow simply treats it as an entry workflow.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-statements"></a>[SC] Statements

<table>
  <tr><td>
<strong>[SC] Statements</strong><br/>
Reference for Statements.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Statements.

#### Related Terms
- Statements

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Statements can be separated by either a newline or a semi-colon:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-string-interpolation"></a>[SC] String interpolation

<table>
  <tr><td>
<strong>[SC] String interpolation</strong><br/>
There is an important difference between single-quoted and double-quoted
strings: Double-quoted strings support variable interpolations, while
single-quoted strings do not.<br/>
  </td></tr>
</table>

**At a glance:** There is an important difference between single-quoted and
double-quoted strings: Double-quoted strings support variable interpolations,
while single-quoted strings do not.

#### Related Terms
- String interpolation

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>There is an important difference between single-quoted and double-quoted strings: Double-quoted strings support variable interpolations, while single-quoted strings do not.</li>
  <li>In practice, double-quoted strings can contain the value of an arbitrary variable by prefixing its name with the $ character, or the value of any expression by using the ${expression} syntax, similar to Bash/shell scripts:</li>
  <li>This code prints:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-string-replacement"></a>[SC] String replacement

<table>
  <tr><td>
<strong>[SC] String replacement</strong><br/>
Reference for String replacement.<br/>
  </td></tr>
</table>

**At a glance:** Reference for String replacement.

#### Related Terms
- String replacement

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>To replace pattern occurrences in a given string, use the replaceFirst and replaceAll methods:</li>
  <li>To remove part of a string, simply replace it with a blank string:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-strings"></a>[SC] Strings

<table>
  <tr><td>
<strong>[SC] Strings</strong><br/>
Reference for Strings.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Strings.

#### Related Terms
- Strings

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Strings can be defined by enclosing text in single or double quotes ( &#x27; or &quot; characters):</li>
  <li>Strings can be concatenated with + :</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-ternary-expression"></a>[SC] Ternary expression

<table>
  <tr><td>
<strong>[SC] Ternary expression</strong><br/>
Reference for Ternary expression.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Ternary expression.

#### Related Terms
- Ternary expression

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A ternary expression consists of a test expression , a true expression , and a false expression , separated by a question mark and a colon:</li>
  <li>If the test expression is true, the true expression is evaluated, otherwise the false expression is evaluated.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-throw"></a>[SC] throw

<table>
  <tr><td>
<strong>[SC] throw</strong><br/>
Reference for throw.<br/>
  </td></tr>
</table>

**At a glance:** Reference for throw.

#### Related Terms
- throw

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A throw statement consists of the throw keyword followed by an expression that returns an error type:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-trycatch"></a>[SC] try/catch

<table>
  <tr><td>
<strong>[SC] try/catch</strong><br/>
Reference for try/catch.<br/>
  </td></tr>
</table>

**At a glance:** Reference for try/catch.

#### Related Terms
- try/catch

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A try/catch statement consists of a try block followed by any number of catch clauses :</li>
  <li>The try block will be executed, and if an error is raised and matches the expected error type of a catch clause, the code in that catch clause will be executed.</li>
  <li>If no catch clause is matched, the error will be raised to the next enclosing try/catch statement, or to the Nextflow runtime.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-tuples"></a>[SC] Tuples

<table>
  <tr><td>
<strong>[SC] Tuples</strong><br/>
Tuples are used to store a fixed sequence of heterogeneous values.<br/>
  </td></tr>
</table>

**At a glance:** Tuples are used to store a fixed sequence of heterogeneous
values.

#### Related Terms
- Tuples

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Tuples are used to store a fixed sequence of heterogeneous values.</li>
  <li>They are created using the tuple function:</li>
  <li>Tuple elements are accessed by index:</li>
  <li>Tuples can be destructured in assignments:</li>
  <li>As well as closure parameters:</li>
  <li>See Tuple for the set of available tuple operations.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Tuples are immutable a once a tuple is created, its elements cannot be modified.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-unary-expressions"></a>[SC] Unary expressions

<table>
  <tr><td>
<strong>[SC] Unary expressions</strong><br/>
Reference for Unary expressions.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Unary expressions.

#### Related Terms
- Unary expressions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A unary expression consists of a unary operator followed by an expression:</li>
  <li>The following unary operators are available:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>~ : bitwise NOT</li>
  <li>! : logical NOT</li>
  <li>+ : unary plus</li>
  <li>- : unary minus</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="script-language-variables"></a>[SC] Variables

<table>
  <tr><td>
<strong>[SC] Variables</strong><br/>
Reference for Variables.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Variables.

#### Related Terms
- Variables

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Variables are declared using the def keyword:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [MD] Modules

### <a id="modules-multiple-inclusions"></a>[MD] Multiple inclusions

<table>
  <tr><td>
<strong>[MD] Multiple inclusions</strong><br/>
A Nextflow script can include any number of modules, and an include statement
can import any number of definitions from a module.<br/>
  </td></tr>
</table>

**At a glance:** A Nextflow script can include any number of modules, and an
include statement can import any number of definitions from a module.

#### Related Terms
- Multiple inclusions

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>A Nextflow script can include any number of modules, and an include statement can import any number of definitions from a module.</li>
  <li>Multiple definitions can be included from the same module by using the syntax shown below:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="modules-sharing-modules"></a>[MD] Sharing modules

<table>
  <tr><td>
<strong>[MD] Sharing modules</strong><br/>
Modules are designed to be easy to share and re-use across different pipelines,
which helps eliminate duplicate work and spread improvements throughout the
community.<br/>
  </td></tr>
</table>

**At a glance:** Modules are designed to be easy to share and re-use across
different pipelines, which helps eliminate duplicate work and spread
improvements throughout the community.

#### Related Terms
- Sharing modules

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Modules are designed to be easy to share and re-use across different pipelines, which helps eliminate duplicate work and spread improvements throughout the community.</li>
  <li>While Nextflow does not provide an explicit mechanism for sharing modules, there are several ways to do it:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>Simply copy the module files into your pipeline repository</li>
  <li>Use Git submodules to fetch modules from other Git repositories without maintaining a separate copy</li>
  <li>Use the nf-core CLI to install and update modules with a standard approach used by the nf-core community</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

## [FL] Files

### <a id="files-files"></a>[FL] Files

<table>
  <tr><td>
<strong>[FL] Files</strong><br/>
Reference for Getting file attributes.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Getting file attributes.

#### Related Terms
- Getting file attributes
- Reading and writing an entire file
- Appending to a file
- Reading a file line by line
- Advanced file reading
- Advanced file writing
- Remote file staging

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The file() method returns a Path , which has several methods for retrieving metadata about the file:</li>
  <li>See the Path reference for the list of available methods.</li>
  <li>Given a file variable, created with the file() method as shown previously, reading a file is as easy as getting the fileas text property, which returns the file content as a string:</li>
  <li>Similarly, you can save a string to a file by assigning it to the fileas text property:</li>
  <li>Binary data can be managed in the same way, just using the file property bytes instead of text .</li>
  <li>Thus, the following example reads the file and returns its content as a byte array:</li>
  <li>Or you can save a byte array to a file:</li>
  <li>In order to append a string value to a file without erasing existing content, you can use the append() method:</li>
  <li>Or use the left shift operator, a more idiomatic way to append text content to a file:</li>
  <li>In order to read a text file line by line you can use the method readLines() provided by the file object, which returns the file content as a list of strings:</li>
  <li>This can also be written in a more idiomatic syntax:</li>
  <li>The classes Reader and InputStream provide fine-grained control for reading text and binary files, respectively.</li>
  <li>The method newReader() creates a Reader object for the given file that allows you to read the content as single characters, lines or arrays of characters:</li>
  <li>The method withReader() works similarly, but automatically calls the close() method for you when you have finished processing the file.</li>
  <li>So, the previous example can be written more simply as:</li>
  <li>The methods newInputStream() and withInputStream() work similarly.</li>
  <li>The main difference is that they create an InputStream object useful for writing binary data.</li>
  <li>The Writer and OutputStream classes provide fine-grained control for writing text and binary files, respectively, including low-level operations for single characters or bytes, and support for big files.</li>
  <li>For example, given two file objects sourceFile and targetFile , the following code copies the first fileas content into the second file, replacing all U characters with X :</li>
  <li>When a process input file resides on a different file system than the work directory, Nextflow copies the file into the work directory using an appropriate Java SDK.</li>
  <li>Remote files are staged in a subdirectory of the work directory with the form stage-&lt;session-id&gt;/&lt;hash&gt;/&lt;filename&gt; , where &lt;hash&gt; is determined by the remote file path.</li>
  <li>If multiple tasks request the same remote file, the file will be downloaded once and reused by each task.</li>
  <li>These files can be reused by resumed runs with the same session ID.</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>To process a big file, use the method eachLine() , which reads only a single line at a time into memory:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-copying-files"></a>[FL] Copying files

<table>
  <tr><td>
<strong>[FL] Copying files</strong><br/>
Reference for Copying files.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Copying files.

#### Related Terms
- Copying files

<details>
<summary>Show full details</summary>

<h4>Constraints</h4>
<ul>
  <li>In general, you should not need to manually copy files, because Nextflow will automatically stage files in and out of the task environment based on the definition of process inputs and outputs.</li>
  <li>Ideally, any operation which transforms files should be encapsulated in a process, in order to leverage Nextflowas staging capabilities as much as possible.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-filesystem-operations"></a>[FL] Filesystem operations

<table>
  <tr><td>
<strong>[FL] Filesystem operations</strong><br/>
Methods for performing filesystem operations such as copying, deleting, and
directory listing are documented in the Path reference.<br/>
  </td></tr>
</table>

**At a glance:** Methods for performing filesystem operations such as copying,
deleting, and directory listing are documented in the Path reference.

#### Related Terms
- Filesystem operations

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Methods for performing filesystem operations such as copying, deleting, and directory listing are documented in the Path reference.</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-listing-directories"></a>[FL] Listing directories

<table>
  <tr><td>
<strong>[FL] Listing directories</strong><br/>
Reference for Listing directories.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Listing directories.

#### Related Terms
- Listing directories

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>The simplest way to list a directory is to use list() or listFiles() , which return a collection of first-level elements (files and directories) of a directory:</li>
  <li>As with other each*() methods, eachFile() takes a closure as a parameter:</li>
</ul>

<h4>Constraints</h4>
<ul>
  <li>Additionally, the eachFile() method allows you to iterate through the first-level elements only (just like listFiles() ).</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-opening-files"></a>[FL] Opening files

<table>
  <tr><td>
<strong>[FL] Opening files</strong><br/>
Reference for Opening files.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Opening files.

#### Related Terms
- Opening files

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>To access and work with files, use the file() method, which returns a file system object given a file path string:</li>
  <li>The file() method can reference both files and directories, depending on what the string path refers to in the file system.</li>
  <li>When using the wildcard characters * , ?</li>
  <li>, [] and {} , the argument is interpreted as a glob path matcher and the file() method returns a list object holding the paths of files whose names match the specified pattern, or an empty list if no match is found:</li>
  <li>By default, wildcard characters do not match directories or hidden files.</li>
  <li>For example, if you want to include hidden files in the result list, enable the hidden option:</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-reading-and-writing"></a>[FL] Reading and writing

<table>
  <tr><td>
<strong>[FL] Reading and writing</strong><br/>
Reference for Reading and writing.<br/>
  </td></tr>
</table>

**At a glance:** Reference for Reading and writing.

#### Related Terms
- Reading and writing

<details>
<summary>Show full details</summary>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

### <a id="files-remote-files"></a>[FL] Remote files

<table>
  <tr><td>
<strong>[FL] Remote files</strong><br/>
Nextflow works with many types of remote files and objects using the same
interface as for local files.<br/>
  </td></tr>
</table>

**At a glance:** Nextflow works with many types of remote files and objects
using the same interface as for local files.

#### Related Terms
- Remote files

<details>
<summary>Show full details</summary>

<h4>Explanation</h4>
<ul>
  <li>Nextflow works with many types of remote files and objects using the same interface as for local files.</li>
  <li>The following protocols are supported:</li>
  <li>To reference a remote file, simply specify the URL when opening the file:</li>
  <li>It can then be used in the same way as a local file:</li>
</ul>

<h4>Allowed Elements</h4>
<ul>
  <li>HTTP(S)/FTP ( http:// , https:// , ftp:// )</li>
  <li>Amazon S3 ( s3:// )</li>
  <li>Azure Blob Storage ( az:// )</li>
  <li>Google Cloud Storage ( gs:// )</li>
</ul>

</details>

[Back to top](#nextflow-syntax-mapped-combined-sources)

---

