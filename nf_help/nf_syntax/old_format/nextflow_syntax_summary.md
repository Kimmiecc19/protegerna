# Nextflow Syntax Summary

Concise reference of grouped terms by category with brief definitions.

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

## Workflow

- **Workflow**: A workflow can be a named workflow or an entry workflow . (aliases: workflow, Entry workflow, Process and workflow recursion, ...)
- **Params**: The params block consists of one or more parameter declarations . (aliases: Parameter (legacy))
- **Output**: The output block consists of one or more output declarations . (aliases: Output variables ( val ), Output files ( path ), Multiple output files, ...)
- **And &**: Reference for And &.
- **Calling processes and workflows**: Reference for Calling processes and workflows.
- **Index files**: Each output can create an index file of the values that were published.
- **Legacy parameters**: Reference for Legacy parameters.
- **Named workflows**: Reference for Named workflows.
- **Parameters**: Parameters can be declared in a Nextflow script with the params block or with legacy parameter declarations.
- **Pipe |**: Reference for Pipe |.
- **Publishing files**: Reference for Publishing files.
- **Special operators**: The following operators have a special meaning when used in a workflow with process and workflow calls.
- **Takes and emits**: Reference for Takes and emits.

## Process

- **Modules**: Environment Modules is a package manager that allows you to dynamically configure your execution environment and easily switch between multiple versions of the same software tool. (aliases: Module inclusion, Module directory, Module aliases, ...)
- **Files**: Reference for Getting file attributes. (aliases: Reading and writing an entire file, Appending to a file, Reading a file line by line, ...)
- **Environment Variables**: The env qualifier allows you to define an environment variable in the process execution context based on the input value.
- **accelerator**: The accelerator directive allows you to request hardware accelerators (e.g.
- **afterScript**: The afterScript directive allows you to execute a custom (Bash) snippet immediately after the main process has run.
- **arch**: The arch directive allows you to define the CPU architecture to build the software in use by the processa task.
- **array**: The array directive allows you to submit tasks as job arrays for executors that support it.
- **beforeScript**: The beforeScript directive allows you to execute a custom (Bash) snippet before the main process script is run.
- **cache**: The cache directive allows you to store the process results to a local cache.
- **clusterOptions**: The clusterOptions directive allows the usage of any native configuration option accepted by your cluster submit command.
- **conda**: The conda directive allows for the definition of the process dependencies using the Conda package manager.
- **Conditional scripts**: The script section is like a function that returns a string.
- **container**: The container directive allows you to execute the process script in a Docker container.
- **containerOptions**: The containerOptions directive allows you to specify any container execution option supported by the underlying container engine (ie.
- **cpus**: Reference for cpus.
- **debug**: By default the stdout produced by the commands executed in all processes is ignored.
- **Directives**: Directives are optional settings that affect the execution of the current process.
- **disk**: The disk directive allows you to define how much local disk storage the process is allowed to use.
- **Dynamic directives**: A directive can be assigned dynamically , during the process execution, so that its actual value can be evaluated based on the process inputs.
- **Dynamic retry with backoff**: network congestion.
- **Dynamic task resources**: Itas a very common scenario that different instances of the same process may have very different needs in terms of computing resources.
- **Dynamic task resources with previous execution trace**: Task resource requests can be updated relative to the trace record metrics of the previous task attempt.
- **echo**: Reference for echo.
- **errorStrategy**: The errorStrategy directive allows you to define how the process manages an error condition.
- **executor**: The executor defines the underlying system where processes are executed.
- **ext**: The ext is a special directive used as namespace for user custom process directives.
- **fair**: The fair directive, when enabled, guarantees that process outputs will be emitted in the order in which they were received.
- **Generic options**: Reference for Generic options.
- **Input files ( path )**: The path qualifier allows you to provide input files to the process execution context.
- **Input repeaters ( each )**: The each qualifier allows you to repeat the execution of a process for each item in a collection, each time a new value is received.
- **Input tuples ( tuple )**: The tuple qualifier groups multiple values into a single input definition.
- **Input variables ( val )**: The val qualifier accepts any data type.
- **Inputs**: The input section defines the input of a process, similar to function arguments.
- **Inputs and outputs (legacy)**: Reference for Inputs and outputs (legacy).
- **Inputs and outputs (typed)**: Reference for Inputs and outputs (typed).
- **label**: The label directive allows the annotation of processes with mnemonic identifier of your choice.
- **machineType**: The machineType can be used to specify a predefined Google Compute Platform machine type when running using the Google Batch , or when using the autopools feature of the Azure Batch executor .
- **maxErrors**: The maxErrors directive allows you to specify the maximum number of times a process can fail when using the retry error strategy.
- **maxForks**: The maxForks directive allows you to define the maximum number of process instances that can be executed in parallel.
- **maxRetries**: The maxRetries directive allows you to define the maximum number of times a process instance can be re-submitted in case of failure.
- **maxSubmitAwait**: The maxSubmitAwait directive allows you to specify how long a task can remain in submission queue without being executed.
- **memory**: The memory directive allows you to define how much memory the process is allowed to use.
- **Multiple input files**: A path input can also accept a collection of files instead of a single value.
- **Multiple inputs**: A process can declare multiple inputs, which allows it to accept inputs from multiple dataflow sources.
- **Naming outputs**: The emit option is used to define the name of a process output, which can be used to access the output by name in the calling workflow.
- **Native execution**: The exec section executes the given code without launching a job.
- **Optional outputs**: Normally, if a specified output is not produced by the task, the task will fail.
- **Outputs**: Reference for Outputs.
- **penv**: The penv directive allows you to define the parallel environment to be used when submitting a parallel task to the SGE resource manager.
- **pod**: The pod directive allows the definition of pod specific settings, such as environment variables, secrets, and config maps, when using the Kubernetes executor.
- **publishDir**: The publishDir directive allows you to publish the process output files to a specified folder.
- **queue**: The queue directive allows you to set the queue where jobs are scheduled when using a grid based executor in your pipeline.
- **resourceLabels**: The resourceLabels directive allows you to specify custom name-value pairs that Nextflow applies to the computing resource used to carry out the process execution.
- **resourceLimits**: The resourceLimits directive allows you to specify environment-specific limits for task resource requests.
- **scratch**: The scratch directive allows you to execute the process in a temporary folder that is local to the execution node.
- **Script**: The script section defines, as a string expression, the script that is executed by the process.
- **Scripts A la carte**: The process script is interpreted by Nextflow as a Bash script by default, but you are not limited to Bash.
- **secret**: The secret directive allows a process to access secrets.
- **shell**: The shell directive allows you to define a custom shell command for process scripts.
- **Shell**: The shell section is a string expression that defines the script that is executed by the process.
- **Singleton outputs**: Reference for Singleton outputs.
- **spack**: The spack directive allows for the definition of the process dependencies using the Spack package manager.
- **Stage directives**: Reference for Stage directives.
- **stageInMode**: The stageInMode directive defines how input files are staged into the process work directory.
- **stageOutMode**: The stageOutMode directive defines how output files are staged out from the scratch directory to the process work directory.
- **Standard input ( stdin )**: The stdin qualifier allows you to forward the input value to the standard input of the process script.
- **storeDir**: The storeDir directive allows you to define a directory that is used as a permanent cache for your process results.
- **Stub**: Reference for Stub.
- **tag**: The tag directive allows you to associate each process execution with a custom label, so that it will be easier to identify them in the log file or in the trace execution report.
- **Task properties**: Reference for Task properties.
- **Template**: Process scripts can be externalized to template files, which allows them to be reused across different processes and tested independently from the pipeline execution.
- **time**: The time directive allows you to define how long a process is allowed to run.
- **Using task directive values**: The task object also contains the values of all process directives for the given task, which allows you to access these settings at runtime.
- **When**: The condition can be any expression that returns a boolean value.

## Channel

- **Channels**: A dataflow channel (or simply channel ) is an asynchronous sequence of values.
- **empty**: The channel.empty factory method, by definition, creates a channel that doesn't emit any value.
- **Factories**: A channel can be created by factories in the channel namespace.
- **from**: Reference for from.
- **fromFilePairs**: The channel.fromFilePairs method creates a channel emitting the file pairs matching a glob pattern provided by the user.
- **fromLineage**: Reference for fromLineage.
- **fromList**: Reference for fromList.
- **fromPath**: You can create a channel emitting one or more file paths by using the channel.fromPath method and specifying a path string as an argument.
- **fromSRA**: The channel.fromSRA method queries the NCBI SRA database and returns a channel emitting the FASTQ files matching the specified criteria i.e project or accession number(s).
- **interval**: The interval method emits an incrementing index (starting from zero) at a periodic interval.
- **of**: Reference for of.
- **Operators**: Operators are symbols that perform specific functions on one or more values, and generally make code easier to read.
- **topic**: A topic channel is a channel that can receive values from many sources implicitly based on a matching topic name .
- **value**: The channel.value function creates a dataflow value bound to the given argument.
- **Values**: A dataflow value is an asynchronous value.
- **watchPath**: The channel.watchPath method watches a folder for one or more files matching a specified pattern.

## Operator

- **branch**: Returns: multiple channels
- **buffer**: Returns: channel
- **collate**: Returns: channel
- **collect**: Returns: dataflow value
- **collectFile**: Returns: channel
- **combine**: Returns: channel
- **concat**: Returns: channel
- **count**: Returns: dataflow value
- **countFasta**: Returns: dataflow value
- **countFastq**: Returns: dataflow value
- **countJson**: Returns: dataflow value
- **countLines**: Returns: dataflow value
- **cross**: Returns: channel
- **distinct**: Returns: channel
- **dump**: Returns: channel
- **filter**: Returns: channel
- **first**: Returns: dataflow value
- **flatMap**: Returns: channel
- **flatten**: Returns: channel
- **groupTuple**: Returns: channel
- **ifEmpty**: Returns: channel
- **join**: Returns: channel
- **last**: Returns: dataflow value
- **map**: Returns: channel
- **max**: Returns: dataflow value
- **merge**: Returns: channel
- **min**: Returns: dataflow value
- **mix**: Returns: channel
- **multiMap**: Returns: multiple channels
- **randomSample**: Returns: channel
- **reduce**: Returns: dataflow value
- **set**: Returns: nothing
- **splitCsv**: Returns: channel
- **splitFasta**: Returns: channel
- **splitFastq**: Returns: channel
- **splitJson**: Returns: channel
- **splitText**: Returns: channel
- **subscribe**: Returns: nothing
- **sum**: Returns: dataflow value
- **take**: Returns: channel
- **tap**: Returns: channel
- **toInteger**: Returns: channel
- **toList**: Returns: dataflow value
- **toSortedList**: Returns: dataflow value
- **transpose**: Returns: channel
- **unique**: Returns: channel
- **until**: Returns: channel
- **view**: Returns: channel

## CLI

- **Config**: Print the resolved pipeline configuration. (aliases: Executor-specific configuration)
- **auth**: Manage Seqera Platform authentication.
- **clean**: Clean up cache and work directories.
- **clone**: Clone a remote project into a folder.
- **Commands**: Reference for Commands.
- **console**: Launch the Nextflow interactive console.
- **drop**: Delete the local copy of a project.
- **fs**: Perform basic filesystem operations.
- **help**: Print the top-level help or specific help for a command.
- **info**: Print project or system runtime information.
- **inspect**: Inspect process settings in a pipeline project.
- **kuberun**: Launch a Nextflow pipeline on a Kubernetes cluster.
- **launch**: Launch a workflow in Seqera Platform .
- **lineage**: Inspect lineage metadata for Nextflow runs.
- **lint**: Lint Nextflow scripts and config files.
- **list**: List all downloaded projects.
- **log**: Print the execution history and log information.
- **Options**: The top-level options are meant to be invoked in relation to the core Nextflow application and are applied to all commands.
- **plugin**: Manage plugins and run plugin-specific commands.
- **pull**: Download or update a project.
- **run**: Execute a pipeline.
- **secrets**: Manage pipeline secrets .
- **self-update**: Update the nextflow runtime to the latest available version.

## Config

- **apptainer**: The apptainer scope controls how Apptainer containers are executed by Nextflow.
- **aws**: The aws scope controls the interactions with AWS, including AWS Batch and S3.
- **azure**: The azure scope allows you to configure the interactions with Azure, including Azure Batch and Azure Blob Storage.
- **charliecloud**: The charliecloud scope controls how Charliecloud containers are executed by Nextflow.
- **dag**: The dag scope controls the workflow diagram generated by Nextflow.
- **docker**: The docker scope controls how Docker containers are executed by Nextflow.
- **env**: The env scope allows the definition one or more variables that will be exported into the environment where workflow tasks are executed.
- **Executor-specific defaults**: Some executor settings have different default values depending on the executor.
- **fusion**: The fusion scope provides advanced configuration for the use of the Fusion file system .
- **google**: The google scope allows you to configure the interactions with Google Cloud, including Google Cloud Batch and Google Cloud Storage.
- **Java settings**: Reference for Java settings.
- **k8s**: The k8s scope controls the deployment and execution of workflow applications in a Kubernetes cluster.
- **mail**: The mail scope controls the mail server used to send email notifications.
- **manifest**: The manifest scope allows you to define some metadata that is useful when publishing or running your pipeline.
- **nextflow**: Reference for nextflow.
- **Nextflow settings**: Reference for Nextflow settings.
- **notification**: The notification scope controls the automatic sending of an email notification on workflow completion.
- **Other settings**: Reference for Other settings.
- **podman**: The podman scope controls how Podman containers are executed by Nextflow.
- **report**: The report scope allows you to configure the workflow Execution report .
- **sarus**: The sarus scope controls how Sarus containers are executed by Nextflow.
- **Seqera Platform settings**: Reference for Seqera Platform settings.
- **shifter**: The shifter scope controls how Shifter containers are executed by Nextflow.
- **singularity**: The singularity scope controls how Singularity containers are executed by Nextflow.
- **timeline**: The timeline scope controls the execution timeline report generated by Nextflow.
- **tower**: The tower scope controls the settings for Seqera Platform (formerly Tower Cloud).
- **trace**: The trace scope controls the layout of the execution trace file generated by Nextflow.
- **Unscoped options**: Reference for Unscoped options.
- **wave**: The wave scope provides advanced configuration for the use of Wave containers .

## Types

- **Channel**: A channel (also known as a dataflow channel or queue channel ) is an asynchronous sequence of values of type E .
- **Bag<E>**: Implements the Iterable<E> trait.
- **Boolean**: Reference for Boolean.
- **Duration**: A Duration represents a duration of time with millisecond precision.
- **Float**: A float is a floating-point number (i.e.
- **Integer**: An integer is a whole number that can be positive or negative.
- **Iterable<E>**: Implemented by the following types: Bag<E> , List<E> , Set<E>
- **List<E>**: Implements the Iterable<E> trait.
- **Map<K,V>**: A map associates or maps keys of type K to values of type V .
- **MemoryUnit**: A MemoryUnit represents a quantity of bytes.
- **Operations**: A Path is a handle for hierarchichal paths such as local files and directories, HTTP/FTP URLs, and object storage paths (e.g.
- **Set<E>**: Implements the Iterable<E> trait.
- **String**: Reference for String.
- **Tuple**: A tuple is a fixed sequence of values, where each value can have its own type.
- **Value<V>**: A dataflow value (also known as a value channel ) is an asynchronous value of type V .
- **VersionNumber**: A VersionNumber represents a semantic or calendar version number.

## Script Language

- **Process**: A process consists of a name and a body. (aliases: Process (typed))
- **Function**: Reference for Function. (aliases: Function call)
- **Enum**: An enum type declaration consists of a name and a body.
- **Variable**: Reference for Variable declaration. (aliases: Variable)
- **Assignment**: Reference for Assignment.
- **Include**: Reference for Include.
- **Feature flag**: A feature flag declaration is an assignment.
- **Shebang**: Reference for Shebang.
- **assert**: Reference for assert.
- **Binary expressions**: Reference for Binary expressions.
- **Capturing groups**: You can match a pattern that includes groups.
- **Closure**: Reference for Closure.
- **Closures**: A closure is a function that can be used like a regular value.
- **Comments**: A line comment starts with // and includes the rest of the line.
- **Conditional execution**: One of the most important features of any programming language is the ability to execute different code under different conditions.
- **Constructor call**: Reference for Constructor call.
- **Deprecations**: Reference for Deprecations.
- **Dynamic string**: Reference for Dynamic string.
- **Expression statement**: Any expression can be a statement.
- **Expressions**: An expression represents a value.
- **Hello world**: Reference for Hello world.
- **if/else**: An if/else statement consists of an if branch and an optional else branch .
- **Index expression**: Reference for Index expression.
- **List**: Reference for List.
- **Lists**: Reference for Lists.
- **Map**: A map literal consists of a comma-separated list of one or more map entries , enclosed in square brackets.
- **Maps**: Maps are used to store associative arrays (also known as dictionaries ).
- **Multi-line strings**: Reference for Multi-line strings.
- **Null**: The null literal is specified as null .
- **Number**: A number literal can be an integer or floating-point number, and can be positive or negative.
- **Parentheses**: Reference for Parentheses.
- **Precedence**: Reference for Precedence.
- **Property expression**: Reference for Property expression.
- **Regular expressions**: Regular expressions are the Swiss Army knife of text processing.
- **return**: Reference for return.
- **Script declarations**: Reference for Script declarations.
- **Script definitions**: So far, we have been focusing on the basic building blocks of Nextflow code, like variables, lists, strings, and closures.
- **Statements**: Reference for Statements.
- **String interpolation**: There is an important difference between single-quoted and double-quoted strings: Double-quoted strings support variable interpolations, while single-quoted strings do not.
- **String replacement**: Reference for String replacement.
- **Strings**: Reference for Strings.
- **Ternary expression**: Reference for Ternary expression.
- **throw**: Reference for throw.
- **try/catch**: Reference for try/catch.
- **Tuples**: Tuples are used to store a fixed sequence of heterogeneous values.
- **Unary expressions**: Reference for Unary expressions.
- **Variables**: Reference for Variables.

## Modules

- **Multiple inclusions**: A Nextflow script can include any number of modules, and an include statement can import any number of definitions from a module.
- **Sharing modules**: Modules are designed to be easy to share and re-use across different pipelines, which helps eliminate duplicate work and spread improvements throughout the community.

## Files

- **Copying files**: Reference for Copying files.
- **Filesystem operations**: Methods for performing filesystem operations such as copying, deleting, and directory listing are documented in the Path reference.
- **Listing directories**: Reference for Listing directories.
- **Opening files**: Reference for Opening files.
- **Reading and writing**: Reference for Reading and writing.
- **Remote files**: Nextflow works with many types of remote files and objects using the same interface as for local files.

