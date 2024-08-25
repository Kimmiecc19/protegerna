# Stratified Sampling (to Minimize Batch Effects)

Since I have many samples, I need to create batches of these samples for running the nf-core pipelines. 

This is especially important when running nf-core/rnasplice, nf-core/differentialabundance, and nf-core/rnafusion, nf-core/sarek or nf-core/raredisease and nf-core/quantms as I need to compare disease to healthy/disease controls.

**NB:** The AnswerALS team have reported 50 protein samples with high batch effects.

[Data Information](https://dataportal.answerals.org/data-information). 

These samples were therefore removed from the matched samples, leaving *347/396* samples left over.

I have the following relevant information for the data that I want to use:
- participant	
- guid	
- genom	
- rna	
- prot	
- sex	
- ethnicity	
- race	
- diagnosis	
- batch

I need to divide files into 4 batches so each batch has +/- 100 files. 

**Stratified sampling involves random selection within predefined groups:**

- It should minimize selection bias and ensure that the true underlying population structure is represented.
- It should enhance the representation of all identified subgroups within a population, leading to more accurate results in heterogeneous populations.
- This method is efficient because a population being studied may be too large to be analyzed individually, so they are organized into groups with the same features ([DataCamp](https://campus.datacamp.com/courses/analyzing-survey-data-in-python/sampling-and-weighting?ex=4), [GeeksforGeeks](https://www.geeksforgeeks.org/stratified-sampling-in-pandas/)).

#### Key Variables for Stratification

1. **Sex**: Male, Female.
2. **Diagnosis**: Alzheimer's disease, Control, Other.
3. **Sequencing Batch**: 52 different batches.

#### Assigning Patient Samples to Balanced Batches using Stratified Sampling

- Use the stratified sampling method to distribute the samples into different batches for running the nf-core/rnaseq pipeline while maintaining the proportions of the necessary variables.
- This will ensure that each batch of ~100 files has a balanced representation of all the key variables.

---

### Python Script to Stratify Data into Batches using Pandas

```python
import pandas as pd

# Load my data into a DataFrame
# My columns: 'synapse', 'file', 'diagnosis', 'patient', 'sex', 'sample', 'tissue', 'seq_batch'
data = pd.read_table('genome_data.csv') #Same for rna and prot

# Add a column for batch assignment
data['pipeline_batch'] = -1

# Define the number of pipeline execution batches
# I have 773 files 
num_batches = 4  # For batches of around 100 files each
batch_size = len(data) // num_batches

# Stratify (group) the data by key variables: sex, diagnosis, tissue type, and sequencing batch
# Lambda shuffles all the rows within each group with a fixed random seed for reproducibility
strata = data.groupby(['sex', 'diagnosis', 'batch']).apply(lambda x: x.sample(frac=1, random_state=42)).reset_index(drop=True)

# Assign pipeline execution batches to the data while keeping the stratification
# First generate a sequence of numbers from 1 to 9 (batch numbers will start from 1 and not zero) and repeat it over the batch_size (calculated above)
batch_indices = list(range(1, num_batches + 1)) * batch_size

# Assigns a number to each batch
# If the total number of indices is less than the length of the data, append the last batch number
if len(batch_indices) < len(data):
    batch_indices += [num_batches] * (len(data) - len(batch_indices))

# Assign the calculated batch indices to the stratified data
strata['pipeline_batch'] = batch_indices

# Organizes the data so that rows are first ordered by their given batch number and then by the patient within each batch.
data = strata.sort_values(by=['pipeline_batch', 'participant']).reset_index(drop=True)

# Optional: Inspect the pipeline batch distribution
#pipeline_batch_counts = data['pipeline_batch'].value_counts()
#print(pipeline_batch_counts)

# Save the pipeline batch assignment to a csv file
data.to_csv('genom_pipeline_batches.csv', index=False) # Same for rna and prot

```

---
