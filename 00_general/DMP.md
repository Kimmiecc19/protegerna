<div align='justify'>

# Advancing Gene Function and Disease Mechanism Insight through a Containerized Multi-Omics Integration Tool

**Creator:** Kimberly Coetzer - **ORCID:**
[0000-0003-2566-0294](https://orcid.org/0000-0003-2566-0294)
**Principal Investigators:** Kimberly Coetzer, Professor Gerhard Tromp,
Professor Gian Van der Spuy
**Affiliation:** Stellenbosch University ([sun.ac.za](https://www.sun.ac.za))  
**Template:** Digital Curation Centre ([dcc.ac.uk](https://www.dcc.ac.uk))  
**Last Modified:** 02-12-2024  
**Copyright:** The above plan creator(s) have agreed that others may use as much
of the text of this plan as they would like in their own plans, and customize it
as necessary. You do not need to credit the creator(s) as the source of the
language used, but using any of the plan's text does not imply that the
creator(s) endorse, or have any relationship to, your project or proposal
**Start date:** 04-01-2023  
**End date:** 06-30-2025  
**Last modified:** 02-12-2024 

## Project Abstract

The biological mechanisms of a disease can only be partially understood by a
single layer of "omics”, prompting the emergence of multi-omics, a discipline
that integrates diverse omics data layers to enhance the understanding of
disease mechanisms. This approach allows researchers to better understand the
interplay between biomolecules and their functions, bridging the gap between
genotype and phenotype. Despite substantial advancements, interpreting complex
integrated data remains challenging due to heterogeneity. The complexity of
these extensive data analyses also poses obstacles in accurately implementing
computational workflows across different environments, undermining deployment
and reproducibility. Therefore, there is a need for a standardized framework
that can effectively integrate and analyze multi-omics data, provide clear
visualization and interpretation, and be user-friendly. In response to this,
this project aims to develop a containerized tool for multi-omics integration to
uncover gene function and molecular mechanisms in heritable disorders after
identifying causative or contributing variants. This involves appropriate tool
selection, custom gene/protein panel formation from single-omics analyses with
subsequent homology modelling, creating a variant protein database, and finally
developing a multi-omics integration tool. As a test case, publicly available
multi-omics data from patients with amyotrophic lateral sclerosis (ALS) will be
employed as a disease model to develop and validate the tool within Nextflow
using Python and R. ALS is a widely prevalent, fatal neurodegenerative condition
affecting anterior horn motor neurons within the spinal cord and pyramidal cells
of the motor cortex. While extensively studied, the complete genetic and
molecular factors influencing its pathology remain elusive. By using ALS as a
disease model, we seek to contribute to the understanding of its pathogenesis
and potentially identify novel insights into the disease. Beyond the scope of
this project, the tool can be applied across a spectrum of genetic disorders,
accelerating the pace of scientific discoveries and improving patient outcomes.

### Sources
- NCBI ([https://www.ncbi.nlm.nih.gov/](https://www.ncbi.nlm.nih.gov/))
- UCSC ([https://genome.ucsc.edu/](https://genome.ucsc.edu/))
- GENCODE
  ([https://www.gencodegenes.org/human/](https://www.gencodegenes.org/human/))
- UniProt ([https://www.uniprot.org/](https://www.uniprot.org/))
- Ensemble
  ([https://www.ensembl.org/index.html](https://www.ensembl.org/index.html))
- GTEx project
  ([https://gtexportal.org/home/datasets](https://gtexportal.org/home/datasets))
- PRIDE ([https://www.ebi.ac.uk/pride/](https://www.ebi.ac.uk/pride/))
- Biostudies
  ([https://www.ebi.ac.uk/biostudies/](https://www.ebi.ac.uk/biostudies/))
- European Nucleotide Archive (ENA) browser
  ([https://www.ebi.ac.uk/ena/browser/home](https://www.ebi.ac.uk/ena/browser/home))
- The Mount Sinai Brain Bank (MSBB) study
  ([https://adknowledgeportal.synapse.org/](https://adknowledgeportal.synapse.org/))
- NeuroLINCS project
  ([https://lincsproject.org/LINCS/data/overview](https://lincsproject.org/LINCS/data/overview))
- AnswerALS (AALS) database
  ([https://dataportal.answerals.org/home](https://dataportal.answerals.org/home))

# Data Collection

## What data will be collected and/or created?

Each dataset is derived from various sources. Healthy individuals were used to
produce the human reference data (genomic, transcriptomic, and proteomic) and
are available at:

- [NCBI](https://www.ncbi.nlm.nih.gov/)
- [UCSC](https://genome.ucsc.edu/)
- [GENCODE](https://www.gencodegenes.org/human/)
- [UniProt](https://www.uniprot.org/)
- [Ensemble](https://www.ensembl.org/index.html)

The GTEx project ([gtexportal.org](https://gtexportal.org/home/datasets)) data
is a comprehensive public resource that studies tissue-specific gene expression
and regulation. Over 1000 participants had samples taken from 54 non-diseased
tissue locations, for molecular tests including whole genome sequencing (WGS),
whole exome sequencing ( WES), and RNA-Seq. When feasible, sample aliquots were
taken from a variety of organs and pre-selected tissue sites, including the
brain of deceased donors who were not on a ventilator for 24 hours prior to
death (dbGaP Study Accession: phs000424.v4.p1).

The following accession numbers will be used to download healthy patient
proteomics data from the Proteomics Identification Database
([PRIDE](https://www.ebi.ac.uk/pride/)): PXD000561 and PXD010154. For PXD000561,
human tissues were harvested postmortem as part of a rapid autopsy program from
three adult donors for each tissue or obtained from National Disease Research
Interchange (NDRI, PA, USA). All tissues were histologically confirmed to be
normal prior to analysis. Fetal tissues were also obtained where possible.
Additionally, hematopoietic cells were isolated from healthy volunteers
participating in routine plateletpheresis. For PXD010154, twenty-nine human
tissue samples used for mRNA and protein expression analysis were obtained from
the Department of Pathology, Uppsala University Hospital, Uppsala, Sweden, as
part of the sample collection governed by the Uppsala Biobank.

Two additional transcriptomics datasets will be used which are made up of data
from healthy individuals. The following accession numbers will be used to
download this data from Biostudies
([biostudies](https://www.ebi.ac.uk/biostudies/)): E-MTAB-2836 and E-MTAB-513.
For E-MTAB-513, mRNA-Seq datasets were generated from human brain, liver,
kidney, heart, skeletal muscle, and testis, as part of the Illumina Human Body
Map 2.0 Project. For E-MTAB-2836, RNA-seq was conducted on tissue samples from
122 human individuals spanning 32 different tissues in order to examine the
human tissue transcriptome. This dataset is part of the TransQST collection.

The following accession numbers will be used to access whole genome sequencing
(WGS) data from the European Nucleotide Archive (ENA) browser
([ENA](https://www.ebi.ac.uk/ena/browser/home)): PRJEB20654, PRJEB25009, and
PRJEB19931. These datasets consist of samples from the Coriell Institute for
Medical Research which obtains data from various patients around the world for
various research projects. The data chosen is from healthy participants who were
part of research projects on diversity. Access does not need to be requested for
these three sources, and files can be downloaded directly from their
corresponding websites without additional data requests.

The first of the diseased patient multi-omics datasets is The Mount Sinai Brain
Bank (MSBB) study ([synapse.org](https://adknowledgeportal.synapse.org/)). This
study provides genomic, transcriptomic, epigenomic and proteomic data from
multiple brain regions of individuals from the Mount Sinai/JJ Peters VA Medical
Center Brain Bank collection (MSBB–Mount Sinai NIH Neurobiobank), which holds
over 2,040 well-characterized brains. Second is the NeuroLINCS project
([lincsproject.org](https://lincsproject.org/LINCS/data/overview)) where WGS,
RNA-Seq, ATAC-Seq and SWATH-MS were carried out on isolated mRNA, DNA and
protein respectively obtained from induced Plur

ipotent Stem Cell (iPSC) lines. These lines were derived from amyotrophic
lateral sclerosis (ALS), spinal muscular atrophy (SMA) and control (unaffected)
individuals. Finally, the main source of data in this research will be the
AnswerALS (AALS) database
([answerals.org](https://dataportal.answerals.org/home)). Subjects with sporadic
amyotrophic lateral sclerosis (sALS), familial ALS (fALS) and related motor
neuron diseases (referred to as non-ALS motor neuron disease), including those
with primary lateral sclerosis, progressive bulbar palsy, and progressive
muscular atrophy, along with asymptomatic ALS gene mutation carriers were
enrolled in AALS. Age-matched control participants without ALS or a family
history of ALS were also enrolled. At each in-clinic visit, approximately 50–100
ml of blood was collected from each participant. An access request was necessary
for this data to be downloaded, and it is currently being fulfilled. The former
two datasets also require that access be requested, which will be done as needed
in this study.

## How will the data be collected or created?

Genomics and transcriptomics data will be downloaded in fastq and FASTA format.
Proteomics data will be downloaded in RAW and FASTA format. FASTA files are a
processed text-based format for representing either nucleotide or peptide
sequences. Fastq files are a text-based format for storing both a biological
sequence (usually nucleotide sequence) and its corresponding quality scores.
Fastq (genomic/transcriptomic) and RAW (proteomics) files are the raw formats
obtained from the sequencer itself. For Thermo Scientific instruments (mass
spectrometers), all output is encoded in “raw files” with the .RAW extension.
These files contain uncompressed and unprocessed image data. All these files
will be downloaded either directly through the primary website (e.g., NCBI) or
through a secondary source such as the Chorus Project
([chorusproject.org](https://chorusproject.org/)) (proteomics data) or a file
transfer protocol (FTP) site. This is a way to download, upload and transfer
files from one location to another on the internet and between computer systems.
The download protocol will depend on each dataset and its corresponding
guidelines. Data will be downloaded locally and stored in the CHPC as well as an
external hard drive as a backup. Globus ([globus.org](https://www.globus.org/))
will be used to transfer files between the hard drive and CHPC. Only the
investigator (myself), supervisor (Professor Tromp), and co-supervisor
(Professor van der Spuy) will have access to this data. A data management plan
will be implemented for the storing, dissemination, and access of data. This
plan will describe the type of data, data formats and metadata, policies for
access and sharing, policies for re-use and redistribution, and archiving plans.
Related tools, software, and code will also be explained in this document.
FAIRsharing ([fairsharing.org](https://fairsharing.org/)) standards and policies
will be applied throughout this research. Examples of these standards are
Minimum Information About a Bioinformatics investigation (MIABi), bio.tools, and
Common Workflow Language (CWL).

# Documentation and Metadata

- **Data Source Information:** Information about the sources from which the data
  was obtained, including links to the original repositories or databases (e.g.,
  NCBI, PRIDE, ENA), accession numbers, and details on how to access the
  original data.
- **File Formats and Types:** Description of the data formats and types (e.g.,
  fastq, FASTA, RAW) specifying the contents of each file and their relevance to
  genomics, transcriptomics, or proteomics.
- **Data Management Plan:** A plan detailing how the data will be stored,
  disseminated, accessed, and archived. This plan may include policies for
  access, sharing, re-use, and redistribution of the data, along with
  information about tools, software, and code used.
- **FAIR Principles Compliance:** Information on how the data adheres to FAIR
  (Findable, Accessible, Interoperable, Reusable) principles for scientific data
  management.
- **Informed Consent Information:** Details on the informed consent procedures
  or waivers for data obtained from human subjects or patients, including
  approvals from ethical review boards and IRBs.
- **Ethical Compliance:** Information confirming compliance with ethical
  regulations and guidelines regarding data anonymization, patient
  confidentiality, and protection of privacy.
- **Dataset Specifics:** Specific details about each dataset, including the
  purpose of original collection, consent information (if available), and any
  limitations or conditions for data reuse imposed by the original providers.
- **Study Aim and Justification:** A brief description of the study's aims,
  rationale, and justification for utilizing the data, emphasizing the
  research's minimal risk to participants and the importance of data
  transparency and reproducibility.
- **Data Access and Permissions:** Information about access permissions granted
  to the investigators (yourself, supervisor, co-supervisor), methods of data
  transfer (e.g., FTP, Globus), and storage locations (CHPC, external hard
  drive).
- **References and Acknowledgments:** Citations or acknowledgments to the
  original studies, datasets, or repositories used, acknowledging the
  contributions of the data sources.

This documentation and metadata serve to provide clarity, transparency, and
compliance with ethical and legal standards while ensuring proper utilization
and storage of the collected data.

# Ethics and Legal Compliance

## How will ethical issues be managed?

Before being released, each dataset received approval from each study’s
corresponding ethical review board. Each study took further measures to
guarantee the privacy and safety of the patient and the data for those who
needed an access request as is the case with the AnswerALS data. All patient
information has been properly anonymized, and neither I nor my supervisors will
have any access to private information. Each source has made de-identified
information available, including race and age, which will be utilized in
accordance with the provider's data reuse regulations.

Several of the publications related to these datasets simply state that they
made use of publicly available datasets and therefore gave no further
information on consent. Where possible, the original study was identified in
order to determine if informed consent was obtained. Informed consent was not
needed for the reference genomes, transcriptomes and proteomes from GENCODE,
NCBI, UCSC, Ensembl and UniProt.

For the GTEx project data, each donor filled in a “GTEx Informed Consent
Verification Forms for Biospecimen Source Sites (BSS’s)” prior to sample
collection for the GTEx project (available on request). For PXD000561, the study
was approved by the Johns Hopkins University’s Institutional Review Board for
use of human tissues and informed consent was obtained from all subjects from
whom blood samples were obtained for isolation of hematopoietic cells. For
PXD010154, the 29 human tissue samples used for mRNA and protein expression
analysis were obtained from the Department of Pathology, Uppsala University
Hospital, Uppsala, Sweden, as part of the sample collection governed by the
Uppsala Biobank (www.uppsalabiobank.uu.se/en/). All tissue samples were
collected and handled using standards developed in the Human Protein Atlas
(www.proteinatlas.org) and in accordance with Swedish laws and regulations.
Tissue samples were anonymized in agreement with approval and advisory reports
from the Uppsala Ethical Review Board [References #2002‐577, 2005‐338 and
2007‐159 (protein) and #2011‐473 (RNA)]. The need for informed consent was
waived by the ethics committee.

No consent or ethical information was available for the first transcriptomics
dataset (E-MTAB-513) that was a part of the Illumina Human Body Map 2.0 Project.
For the second transcriptomics dataset (EMTAB-2836), the use of human tissue
samples was approved by the Uppsala Ethical Review Board (Reference #2011/473).
Human tissue samples used for protein and mRNA expression analyses were
collected and handled in accordance with Swedish laws and regulations and
obtained from the Department of Pathology, Uppsala University Hospital, Uppsala,
Sweden as part of the sample collection governed by the Uppsala Biobank
(http://www.uppsalabiobank.uu.se/en/). All human tissue samples used in the
study were anonymized in accordance with approval and advisory report from the
Uppsala Ethical Review Board [Reference #2002-577, 2005-338 and 2007-159
(protein) and #2011-473 (RNA)].

For the genomics datasets (PRJEB20654, PRJEB25009, PRJEB19931), DNA samples were
obtained from the Coriell Institute for Medical Research. Each donor had to fill
in a National Institute of General Medical Sciences (NIGMS) human genetic cell
repository informed consent form (available upon request).

The clinical portions of AnswerALS (AALS) were coordinated through Johns Hopkins
University and Massachusetts General Hospital. Johns Hopkins University,
Massachusetts General Hospital, Ohio State, Emory University, Washington
University, Northwestern University, Cedars Sinai, and Texas Neurology were
among the eight participating neuromuscular centres, which were spread out
across the USA. The study was approved by local institutional review boards, and
all participants provided written informed consent prior to undergoing any study
procedures. Consent was uniform across all sites and included an agreement to
share data broadly for medical research.

The Mount Sinai Brain Bank (MSBB) study complied with all ethical regulations
and institutional protocols for studying human postmortem samples. All human
specimens were frozen samples from deceased donors obtained from the NIH
NeuroBioBank. Donor anonymity was preserved, and guidelines were followed
regarding consent, protection of human subjects, and donor confidentiality.
Prior to being shared with the tissue biobank, collection of the pituitary
samples upon death was approved by the Institutional Review Board [IRB
(#HP-00042077)] for the University of Maryland and consent was obtained from all
donors or next of kin. Study #13-00709 PS for tissue repository at the Bronx VA
Medical Center was determined Human Research Exempt by the IRB at the Icahn
School of Medicine at Mount Sinai (ISMMS), as defined by DHHS regulations [45
CFR 46.101(b)]. As these human samples were obtained and de-identified, the
study itself was not considered human subject research by the IRB at the ISMMS,
where the assays were performed.

For the NeuroLINCS dataset, all the cell lines and protocols in the study were
carried out in accordance with the guidelines approved by the Stem Cell Research
Oversight committee (SCRO) and IRB at the Cedars-Sinai Medical Center under the
IRB-SCRO Protocols Pro00032834 (iPSC Core Repository and Stem Cell Program).

## Ethics Review and Compliance

- **Documenting Approval:** Documenting approval or exemption from ethics review
  for each dataset demonstrates a commitment to ethical guidelines.
- **Informed Consent and Anonymization:** Understanding the original data
  source's informed consent process and anonymization techniques applied to the
  datasets is vital. Ensuring that all data utilized has been properly
  anonymized and obtained with appropriate consent or waivers is critical.
- **Data Privacy and Confidentiality:** Ensuring the protection of data privacy
  and confidentiality of participants is essential. Storing the data securely,
  limiting access to authorized personnel, and following protocols for data
  sharing and dissemination as outlined in the data management plan helps
  maintain confidentiality.
- **Transparency and Documentation:** Transparently documenting the data
  sources, methods, and limitations of the study ensures accountability.
  Comprehensive documentation of metadata, data sources, and ethical
  considerations enables clear communication and reproducibility.
- **Responsible Data Use:** Adhering to guidelines and policies established by
  the original data providers regarding data use, redistribution, and
  re-analysis demonstrates ethical responsibility. Complying with terms of use
  and respecting any imposed limitations on data usage is imperative.
- **Continuous Review and Adherence:** Continuously reviewing and updating
  ethical compliance measures throughout the research process is crucial.
  Adhering to evolving ethical standards and promptly addressing any ethical
  concerns that may arise ensures ongoing ethical oversight.
- **Public Transparency and Communication:** Sharing findings transparently and
  responsibly, acknowledging data sources, and maintaining open communication
  with the scientific community and stakeholders about the research's ethical
  aspects enhances credibility and accountability.
- **Ethics Committee Consultation:** Seeking guidance or consultation from an
  ethics committee or expert reviewers when ethical dilemmas or uncertainties
  arise can provide valuable insights and ensure adherence to ethical best
  practices.
- **Risk Assessment and Mitigation:** Conducting a thorough risk assessment to
  identify potential ethical risks associated with data use and implementing
  mitigation strategies to minimize any identified risks.

## Copyright and Intellectual Property Rights (IP/IPR) Management

- **Understanding Terms of Use:** Review the terms of use, licenses, and
  agreements associated with each dataset. Adhere to these terms strictly.
- **Respect Copyright and Licensing:** Respect the copyright and licensing terms
  of the original datasets. Acknowledge the original data sources appropriately
  in publications, presentations, and any derivative works.
- **Non-Commercial Usage:** Ensure compliance with restrictions on commercial
  usage if applicable.
- **Derivative Works and Modifications:** Understand whether the dataset allows
  for derivative works or modifications. Ensure that any changes align with the
  permissions granted by the dataset's license or terms of use.
- **Intellectual Property for Derived Findings:** Consider the intellectual
  property implications of generating new insights, algorithms, or models based
  on the dataset. Determine if the new work is eligible for patenting or
  requires protection.
- **Open Access and Open Science Policies:** Adhere to open access and open
  science principles when feasible. Consider sharing derived data, findings, or
  tools openly, subject to the original dataset's permissions and any ethical
  considerations.
- **Documentation and Records:** Maintain detailed documentation of all data
  sources, permissions, and any modifications made to the datasets. Record the
  specific licenses, terms of use, and any restrictions applied.
- **Attribution and Citations:** Properly attribute the original dataset sources
  in publications, presentations, and any outputs resulting from the research.
  Follow citation guidelines provided by the dataset creators.
- **Responsible Data Sharing:** When sharing or disseminating findings or
  derived data, ensure alignment with the original dataset's policies. Respect
  data provider requirements for sharing and redistribution.
- **Regular Review of Policies:** Periodically review policies regarding data
  use, copyright, and intellectual property rights, adjusting research practices
  accordingly as these policies evolve.

## Storage and Backup

### Practices Implemented:

- **Local Storage and CHPC:**
  - Store data locally on secured servers.
  - Utilize the CHPC (Center for High-Performance Computing) for secure storage
    leveraging its robust infrastructure and security measures.

- **External Hard Drive Backup:**
  - Maintain an external hard drive dedicated to backing up data.
  - Regularly sync local storage with the external drive to ensure redundancy
    and protect against data loss.

- **Cloud-Based Backup Solutions:**
  - Utilize cloud storage services from reputable providers like Amazon S3,
    Google Cloud Storage, or Microsoft Azure as an additional backup option.
  - These services provide secure and scalable storage with built-in redundancy.

- **Automated Backup Procedures:**
  - Implement automated backup procedures to regularly and consistently back up
    data.
  - Scheduled backups, preferably with versioning, ensure that changes and
    updates are captured without manual intervention.

- **Regular Data Integrity Checks:**
  - Periodically verify the integrity of stored data by running checksums or
    integrity checks to ensure data remains intact and uncorrupted over time.

- **Metadata and Documentation:**
  - Accompany stored data with comprehensive metadata and documentation
    detailing data sources, formats, processing steps, and any transformations
    applied.

- **Retention Policies:**
  - Establish clear data retention policies aligned with ethical guidelines and
    project needs.
  - Determine how long different types of data will be stored and when outdated
    or unnecessary data will be securely disposed of.

## Access and Security Management

### Practices Implemented:

- **Access Control Policies:**
  - Develop detailed access control policies defining who can access specific
    datasets, files, or resources.
  - Create user roles and permission levels based on the principle of least
    privilege.

- **Secure Data Transfer Protocols:**
  - Utilize secure transfer protocols (e.g., HTTPS, SFTP, SSH) to prevent
    unauthorized access or interception while moving data between systems.

- **Monitoring and Logging:**
  - Implement logging mechanisms to track data access, modifications, and system
    activities.
  - Regularly review logs to detect any suspicious activities and ensure
    compliance with access policies.

## Selection and Preservation

### Data of Long-Term Value:

- **Genomic, Transcriptomic, and Proteomic Data:**
  - Fundamental for understanding gene function, disease mechanisms, and
    potential therapeutic targets.

- **Multi-Omics Integration Tools and Algorithms:**
  - Tools or algorithms for integrating multi-omics data, such as the
    containerized proteogenomics tool.

- **Annotated Datasets:**
  - Datasets created during research that could serve as benchmarks or
    references for future studies.

- **Derived Insights and Findings:**
  - Summaries of significant findings, insights, and conclusions derived from
    multi-omics datasets.

- **Documentation and Methodologies:**
  - Detailed documentation of methodologies, data processing steps, and analysis
    workflows for reproducibility.

- **Metadata and Descriptive Information:**
  - Metadata describing characteristics, structure, and context of datasets,
    including sample collection, processing, and analysis information.

## Long-Term Preservation Plan

### Strategies Implemented:

- **Data Storage Infrastructure:**
  - Utilization of secure and scalable storage infrastructure capable of
    accommodating large datasets, including local servers, cloud-based
    solutions, or specialized repositories.

- **Data Backups:**
  - Implementation of regular and redundant backup protocols to safeguard
    against data loss.

- **Metadata Management:**
  - Establishment of comprehensive metadata standards and documentation to
    accompany datasets.

- **Data Format Standards:**
  - Storage of datasets in widely accepted, non-proprietary formats for
    long-term compatibility and accessibility.

- **Data Access and Sharing Policies:**
  - Determination and limitation of dataset access based on sensitivity and
    adherence to any embargo periods or usage restrictions.

- **Data Preservation Platform or Repository:**
  - Deposit of datasets into established repositories or archives designed for
    long-term preservation of scientific data.

- **Periodic Review and Maintenance:**
  - Conducting periodic reviews of dataset integrity, relevance, and usability
    to ensure ongoing preservation.

- **Documentation of Preservation Procedures:**
  - Documentation of preservation strategies, including backup schedules,
    metadata updates, and changes in storage or access policies.

## Data Sharing

### Practices Implemented:

- **Data Repository Deposition:**
  - Deposition of datasets in recognized data repositories or archives specific
    to genomics, transcriptomics, and proteomics.

- **Data Access Policies:**
  - Definition of access policies considering dataset sensitivity, with options
    including open access, controlled access, or embargo periods.

- **Metadata Availability:**
  - Provision of comprehensive metadata accompanying datasets for detailed
    descriptions of content and methodologies.

- **Data Licensing:**
  - Definition of licensing terms for data usage to specify how others can use,
    modify, or share the data.

- **Publication of Findings:**
  - Sharing research findings and analyses derived from datasets through
    scientific publications, presentations, or preprint servers.

- **Data Access Portals:**
  - Creation of user-friendly interfaces or portals facilitating easy dataset
    access, including search functionalities and documentation.

- **Collaborative Platforms:**
  - Engagement with collaborative platforms or consortiums focused on similar
    research areas to facilitate data sharing and collaboration.

- **Data Citation and DOI Assignment:**
  - Assignment of Digital Object Identifiers (DOIs) to datasets and associated
    publications to ensure proper citation and recognition.

- **Documentation and Tutorials:**
  - Provision of comprehensive documentation and tutorials guiding users on
    dataset navigation, interpretation, and utilization.

### Restrictions on Data Sharing:

- Access restrictions to ensure only authorized individuals or entities can view
  or use the data.
- Embargo periods before making data fully accessible.
- Legal or ethical obligations dictating restrictions on sharing, especially
  concerning agreements or regulatory requirements.
- Context-specific limitations to prevent misinterpretation or unintended uses
  that could lead to harm or misrepresentation.

</div>
