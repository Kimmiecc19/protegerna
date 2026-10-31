# Nextflow Syntax Summary

A concise, category-first overview of grouped terms with short synopses and
quick lookup links.

![Total
Terms](https://img.shields.io/badge/Total%20Terms-247-0f172a?style=for-the-badge)
![Categories](https://img.shields.io/badge/Categories-10-0ea5e9?style=for-the-badge)

## <a id="summary-category-snapshot"></a>Category Snapshot

| Category | Count | Top Terms |
|---|---|---|
| [Workflow](#workflow) | 13 | Workflow, Params, Output, ... |
| [Process](#process) | 49 | Modules, accelerator, afterScript, ... |
| [Channel](#channel) | 12 | empty, from, fromFilePairs, ... |
| [Operator](#operator) | 48 | branch, buffer, collate, ... |
| [CLI](#cli) | 23 | Config, auth, clean, ... |
| [Config](#config) | 29 | apptainer, aws, azure, ... |
| [Types](#types) | 16 | Channel, Bag, Boolean, ... |
| [Script Language](#script-language) | 48 | Process, Function, Enum, ... |
| [Modules](#modules) | 2 | Multiple inclusions, Sharing modules |
| [Files](#files) | 7 | Files, Copying files, Filesystem operations, ... |

## <a id="summary-category-index"></a>Category Index

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

## <a id="summary-workflow"></a>Workflow

| Term | Synopsis |
|---|---|
| Workflow | A workflow can be a named workflow or an entry workflow . |
| Params | The params block consists of one or more parameter declarations . |
| Output | The output block consists of one or more output declarations . |
| And &amp; | Reference for And &amp;. |
| Calling processes and workflows | Reference for Calling processes and workflows. |
| Index files | Each output can create an index file of the values that were published. |
| Legacy parameters | Reference for Legacy parameters. |
| Named workflows | Reference for Named workflows. |
| Parameters | Parameters can be declared in a Nextflow script with the params block or with legacy parameter declarations. |
| Pipe | | Reference for Pipe |. |
| Publishing files | Reference for Publishing files. |
| Special operators | The following operators have a special meaning when used in a workflow with process and workflow calls. |
| Takes and emits | Reference for Takes and emits. |

## <a id="summary-process"></a>Process

| Term | Synopsis |
|---|---|
| Modules | Environment Modules is a package manager that allows you to dynamically configure your execution environment and easily switch between multiple versions of the same software tool. |
| accelerator | The accelerator directive allows you to request hardware accelerators (e.g. |
| afterScript | The afterScript directive allows you to execute a custom (Bash) snippet immediately after the main process has run. |
| arch | The arch directive allows you to define the CPU architecture to build the software in use by the processa task. |
| array | The array directive allows you to submit tasks as job arrays for executors that support it. |
| beforeScript | The beforeScript directive allows you to execute a custom (Bash) snippet before the main process script is run. |
| cache | The cache directive allows you to store the process results to a local cache. |
| clusterOptions | The clusterOptions directive allows the usage of any native configuration option accepted by your cluster submit command. |
| conda | The conda directive allows for the definition of the process dependencies using the Conda package manager. |
| container | The container directive allows you to execute the process script in a Docker container. |
| containerOptions | The containerOptions directive allows you to specify any container execution option supported by the underlying container engine (ie. |
| cpus | Reference for cpus. |
| debug | By default the stdout produced by the commands executed in all processes is ignored. |
| Directives | Reference for Directives. |
| disk | The disk directive allows you to define how much local disk storage the process is allowed to use. |
| echo | Reference for echo. |
| errorStrategy | The errorStrategy directive allows you to define how the process manages an error condition. |
| executor | The executor defines the underlying system where processes are executed. |
| ext | The ext is a special directive used as namespace for user custom process directives. |
| fair | The fair directive, when enabled, guarantees that process outputs will be emitted in the order in which they were received. |
| Generic options | Reference for Generic options. |
| Inputs | Reference for Inputs. |
| Inputs and outputs (legacy) | Reference for Inputs and outputs (legacy). |
| Inputs and outputs (typed) | Reference for Inputs and outputs (typed). |
| label | The label directive allows the annotation of processes with mnemonic identifier of your choice. |
| machineType | The machineType can be used to specify a predefined Google Compute Platform machine type when running using the Google Batch , or when using the autopools feature of the Azure Batch executor . |
| maxErrors | The maxErrors directive allows you to specify the maximum number of times a process can fail when using the retry error strategy. |
| maxForks | The maxForks directive allows you to define the maximum number of process instances that can be executed in parallel. |
| maxRetries | The maxRetries directive allows you to define the maximum number of times a process instance can be re-submitted in case of failure. |
| maxSubmitAwait | The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue without being executed. |
| memory | The memory directive allows you to define how much memory the process is allowed to use. |
| Outputs | Reference for Outputs. |
| penv | The penv directive allows you to define the parallel environment to be used when submitting a parallel task to the SGE resource manager. |
| pod | The pod directive allows the definition of pod specific settings, such as environment variables, secrets, and config maps, when using the Kubernetes executor. |
| publishDir | The publishDir directive allows you to publish the process output files to a specified folder. |
| queue | The queue directive allows you to set the queue where jobs are scheduled when using a grid based executor in your pipeline. |
| resourceLabels | The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies to the computing resource used to carry out the process execution. |
| resourceLimits | The resourceLimits directive allows you to specify environment-specific limits for task resource requests. |
| scratch | The scratch directive allows you to execute the process in a temporary folder that is local to the execution node. |
| secret | The secret directive allows a process to access secrets. |
| shell | The shell directive allows you to define a custom shell command for process scripts. |
| spack | The spack directive allows for the definition of the process dependencies using the Spack package manager. |
| Stage directives | Reference for Stage directives. |
| stageInMode | The stageInMode directive defines how input files are staged into the process work directory. |
| stageOutMode | The stageOutMode directive defines how output files are staged out from the scratch directory to the process work directory. |
| storeDir | The storeDir directive allows you to define a directory that is used as a permanent cache for your process results. |
| tag | The tag directive allows you to associate each process execution with a custom label, so that it will be easier to identify them in the log file or in the trace execution report. |
| Task properties | Reference for Task properties. |
| time | The time directive allows you to define how long a process is allowed to run. |

## <a id="summary-channel"></a>Channel

| Term | Synopsis |
|---|---|
| empty | The channel.empty factory method, by definition, creates a channel that doesn't emit any value. |
| from | Reference for from. |
| fromFilePairs | The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob pattern provided by the user. |
| fromLineage | Reference for fromLineage. |
| fromList | Reference for fromList. |
| fromPath | You can create a channel emitting one or more file paths by using the channel.fromPath method and specifying a path string as an argument. |
| fromSRA | The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ files matching the specified criteria i.e project or accession number(s). |
| interval | The interval method emits an incrementing index (starting from zero) at a periodic interval. |
| of | Reference for of. |
| topic | A topic channel is a channel that can receive values from many sources implicitly based on a matching topic name . |
| value | The channel.value function creates a dataflow value bound to the given argument. |
| watchPath | The channel.watchPath method watches a folder for one or more files matching a specified pattern. |

## <a id="summary-operator"></a>Operator

| Term | Synopsis |
|---|---|
| branch | Returns: multiple channels |
| buffer | Returns: channel |
| collate | Returns: channel |
| collect | Returns: dataflow value |
| collectFile | Returns: channel |
| combine | Returns: channel |
| concat | Returns: channel |
| count | Returns: dataflow value |
| countFasta | Returns: dataflow value |
| countFastq | Returns: dataflow value |
| countJson | Returns: dataflow value |
| countLines | Returns: dataflow value |
| cross | Returns: channel |
| distinct | Returns: channel |
| dump | Returns: channel |
| filter | Returns: channel |
| first | Returns: dataflow value |
| flatMap | Returns: channel |
| flatten | Returns: channel |
| groupTuple | Returns: channel |
| ifEmpty | Returns: channel |
| join | Returns: channel |
| last | Returns: dataflow value |
| map | Returns: channel |
| max | Returns: dataflow value |
| merge | Returns: channel |
| min | Returns: dataflow value |
| mix | Returns: channel |
| multiMap | Returns: multiple channels |
| randomSample | Returns: channel |
| reduce | Returns: dataflow value |
| set | Returns: nothing |
| splitCsv | Returns: channel |
| splitFasta | Returns: channel |
| splitFastq | Returns: channel |
| splitJson | Returns: channel |
| splitText | Returns: channel |
| subscribe | Returns: nothing |
| sum | Returns: dataflow value |
| take | Returns: channel |
| tap | Returns: channel |
| toInteger | Returns: channel |
| toList | Returns: dataflow value |
| toSortedList | Returns: dataflow value |
| transpose | Returns: channel |
| unique | Returns: channel |
| until | Returns: channel |
| view | Returns: channel |

## <a id="summary-cli"></a>CLI

| Term | Synopsis |
|---|---|
| Config | Print the resolved pipeline configuration. |
| auth | Manage Seqera Platform authentication. |
| clean | Clean up cache and work directories. |
| clone | Clone a remote project into a folder. |
| Commands | Reference for Commands. |
| console | Launch the Nextflow interactive console. |
| drop | Delete the local copy of a project. |
| fs | Perform basic filesystem operations. |
| help | Print the top-level help or specific help for a command. |
| info | Print project or system runtime information. |
| inspect | Inspect process settings in a pipeline project. |
| kuberun | Launch a Nextflow pipeline on a Kubernetes cluster. |
| launch | Launch a workflow in Seqera Platform . |
| lineage | Inspect lineage metadata for Nextflow runs. |
| lint | Lint Nextflow scripts and config files. |
| list | List all downloaded projects. |
| log | Print the execution history and log information. |
| Options | The top-level options are meant to be invoked in relation to the core Nextflow application and are applied to all commands. |
| plugin | Manage plugins and run plugin-specific commands. |
| pull | Download or update a project. |
| run | Execute a pipeline. |
| secrets | Manage pipeline secrets . |
| self-update | Update the nextflow runtime to the latest available version. |

## <a id="summary-config"></a>Config

| Term | Synopsis |
|---|---|
| apptainer | The apptainer scope controls how Apptainer containers are executed by Nextflow. |
| aws | The aws scope controls the interactions with AWS, including AWS Batch and S3. |
| azure | The azure scope allows you to configure the interactions with Azure, including Azure Batch and Azure Blob Storage. |
| charliecloud | The charliecloud scope controls how Charliecloud containers are executed by Nextflow. |
| dag | The dag scope controls the workflow diagram generated by Nextflow. |
| docker | The docker scope controls how Docker containers are executed by Nextflow. |
| env | The env scope allows the definition one or more variables that will be exported into the environment where workflow tasks are executed. |
| Executor-specific defaults | Some executor settings have different default values depending on the executor. |
| fusion | The fusion scope provides advanced configuration for the use of the Fusion file system . |
| google | The google scope allows you to configure the interactions with Google Cloud, including Google Cloud Batch and Google Cloud Storage. |
| Java settings | Reference for Java settings. |
| k8s | The k8s scope controls the deployment and execution of workflow applications in a Kubernetes cluster. |
| mail | The mail scope controls the mail server used to send email notifications. |
| manifest | The manifest scope allows you to define some metadata that is useful when publishing or running your pipeline. |
| nextflow | Reference for nextflow. |
| Nextflow settings | Reference for Nextflow settings. |
| notification | The notification scope controls the automatic sending of an email notification on workflow completion. |
| Other settings | Reference for Other settings. |
| podman | The podman scope controls how Podman containers are executed by Nextflow. |
| report | The report scope allows you to configure the workflow Execution report . |
| sarus | The sarus scope controls how Sarus containers are executed by Nextflow. |
| Seqera Platform settings | Reference for Seqera Platform settings. |
| shifter | The shifter scope controls how Shifter containers are executed by Nextflow. |
| singularity | The singularity scope controls how Singularity containers are executed by Nextflow. |
| timeline | The timeline scope controls the execution timeline report generated by Nextflow. |
| tower | The tower scope controls the settings for Seqera Platform (formerly Tower Cloud). |
| trace | The trace scope controls the layout of the execution trace file generated by Nextflow. |
| Unscoped options | Reference for Unscoped options. |
| wave | The wave scope provides advanced configuration for the use of Wave containers . |

## <a id="summary-types"></a>Types

| Term | Synopsis |
|---|---|
| Channel | A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of values of type E . |
| Bag | Implements the Iterable trait. |
| Boolean | Reference for Boolean. |
| Duration | A Duration represents a duration of time with millisecond precision. |
| Float | A float is a floating-point number (i.e. |
| Integer | An integer is a whole number that can be positive or negative. |
| Iterable | Implemented by the following types: Bag , List , Set |
| List | Implements the Iterable trait. |
| Map | A map associates or maps keys of type K to values of type V . |
| MemoryUnit | A MemoryUnit represents a quantity of bytes. |
| Operations | A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, and object storage paths (e.g. |
| Set | Implements the Iterable trait. |
| String | Reference for String. |
| Tuple | A tuple is a fixed sequence of values, where each value can have its own type. |
| Value | A dataflow value (also known as a value channel ) is an asynchronous value of type V . |
| VersionNumber | A VersionNumber represents a semantic or calendar version number. |

## <a id="summary-script-language"></a>Script Language

| Term | Synopsis |
|---|---|
| Process | A process consists of a name and a body. |
| Function | Reference for Function. |
| Enum | An enum type declaration consists of a name and a body. |
| Variable | Reference for Variable declaration. |
| Assignment | Reference for Assignment. |
| Include | Reference for Include. |
| Feature flag | A feature flag declaration is an assignment. |
| Shebang | Reference for Shebang. |
| assert | Reference for assert. |
| Binary expressions | Reference for Binary expressions. |
| Capturing groups | You can match a pattern that includes groups. |
| Closure | Reference for Closure. |
| Closures | A closure is a function that can be used like a regular value. |
| Comments | A line comment starts with // and includes the rest of the line. |
| Conditional execution | One of the most important features of any programming language is the ability to execute different code under different conditions. |
| Constructor call | Reference for Constructor call. |
| Deprecations | Reference for Deprecations. |
| Dynamic string | Reference for Dynamic string. |
| Expression statement | Any expression can be a statement. |
| Expressions | An expression represents a value. |
| Hello world | Reference for Hello world. |
| if/else | An if/else statement consists of an if branch and an optional else branch . |
| Index expression | Reference for Index expression. |
| List | Reference for List. |
| Lists | Reference for Lists. |
| Map | A map literal consists of a comma-separated list of one or more map entries , enclosed in square brackets. |
| Maps | Maps are used to store associative arrays (also known as dictionaries ). |
| Multi-line strings | Reference for Multi-line strings. |
| Null | The null literal is specified as null . |
| Number | A number literal can be an integer or floating-point number, and can be positive or negative. |
| Operators | Operators are symbols that perform specific functions on one or more values, and generally make code easier to read. |
| Parentheses | Reference for Parentheses. |
| Precedence | Reference for Precedence. |
| Property expression | Reference for Property expression. |
| Regular expressions | Regular expressions are the Swiss Army knife of text processing. |
| return | Reference for return. |
| Script declarations | Reference for Script declarations. |
| Script definitions | So far, we have been focusing on the basic building blocks of Nextflow code, like variables, lists, strings, and closures. |
| Statements | Reference for Statements. |
| String interpolation | There is an important difference between single-quoted and double-quoted strings: Double-quoted strings support variable interpolations, while single-quoted strings do not. |
| String replacement | Reference for String replacement. |
| Strings | Reference for Strings. |
| Ternary expression | Reference for Ternary expression. |
| throw | Reference for throw. |
| try/catch | Reference for try/catch. |
| Tuples | Tuples are used to store a fixed sequence of heterogeneous values. |
| Unary expressions | Reference for Unary expressions. |
| Variables | Reference for Variables. |

## <a id="summary-modules"></a>Modules

| Term | Synopsis |
|---|---|
| Multiple inclusions | A Nextflow script can include any number of modules, and an include statement can import any number of definitions from a module. |
| Sharing modules | Modules are designed to be easy to share and re-use across different pipelines, which helps eliminate duplicate work and spread improvements throughout the community. |

## <a id="summary-files"></a>Files

| Term | Synopsis |
|---|---|
| Files | Reference for Getting file attributes. |
| Copying files | Reference for Copying files. |
| Filesystem operations | Methods for performing filesystem operations such as copying, deleting, and directory listing are documented in the Path reference. |
| Listing directories | Reference for Listing directories. |
| Opening files | Reference for Opening files. |
| Reading and writing | Reference for Reading and writing. |
| Remote files | Nextflow works with many types of remote files and objects using the same interface as for local files. |
