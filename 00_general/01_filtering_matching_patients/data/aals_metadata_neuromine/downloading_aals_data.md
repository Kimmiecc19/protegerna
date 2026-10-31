# Notes for Downloading AnswerALS Data from Neuromine Using CLI

### Data Source

> "Answer ALS was conceived to help fill the knowledge gap by carefully building
> a clinical and in-depth biological picture of ALS from each of over 1000 study
> participants and 200 healthy controls. For each participant, the program
> generates longitudinal clinical data, whole-genome sequences, and multi-omics
> (transcriptomics, epigenomics, and proteomics) from induced pluripotent stem
> cell-derived motor neurons. These data and links to the associated
> bio-resources (patient-derived biofluids, induced pluripotent stem cell (iPSC)
> lines) are made available to the global research community through the Answer
> ALS Neuromine Data Portal."

- [Neuromine](https://dataportal.answerals.org/home)

---

### Data Level Descriptions

**Description of Levels**  
- **Level 1**: Raw, immutable data coming off an instrument (e.g., a sequencer).
  For genomics, we only provide data corresponding to this level upon special
  request.
- **Level 2**: Raw data mapped against the appropriate reference. Genomics (WGS)
  uses hg38 as a reference.
- **Level 3**: The most processed form of patient-specific data.  
- **Level 4**: Data attained from the joining of a cohort of patients’ level 3
  data from a particular assay.
- **Level 5**: Comparative data between two specific cohorts, typically labeled
  as differentially expressed genes (DESeq), proteins, or enriched sites within
  the genome (DiffBind).

We will only be focusing on level one (raw data).

- **Proteomics**: Raw data coming off a mass spectrometer is called a WIFF file
  (~2.5 GB/individual).
- **Genomics**: Raw, immutable data coming off an instrument (e.g., a sequencer)
  is called a FASTQ file. FASTQ is a text-based sequencing data file format that
  stores both raw sequence data and quality scores (~54.5 GB/individual).
- **Transcriptomics**: Raw data coming off an instrument (e.g., a sequencer) is
  also called a FASTQ file (~5 GB/individual).

---

### Data Selection

All of the WGS, proteomic, and transcriptomic data was chosen at level one only
for download and processing.

---

### Data Download from Neuromine

1. First, start a `tmux` session:
    ```bash
    tmux new -s aals_data (tmux attach -t aals_data)
    ```

2. Navigate to the download tool:
    ```bash
    cd /home/kcoetzer/answer-als-download-tool-linux-x64/CLI
    ./downloadtool
    ```

3. Log in to Neuromine:
    ```bash
    ./downloadtool login -u kimberlycoetzer@gmail.com -c 745745
    ```
    `-c` will always change and can be accessed from: [Neuromine
Activation](https://dataportal.answerals.org/activate)

4. Configure the download path:
    ```bash
    ./downloadtool config -s LocalDownloadPath "/home/kcoetzer/DATA/"
    ```

5. Start the download:
    ```bash
    ./downloadtool start -n aals_data  # This is the name chosen on the Neuromine website
    ```

**Note:** Login lasts for approximately 24 hours, after which a new activation
code is needed.

---
