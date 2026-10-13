library(readr)

#-----------------------------
# Input files
#-----------------------------
samplesheet_file <- "diffab_quantms_samplesheet_batch1.csv"
matrix_file      <- "diann_report.pg_matrix.tsv"

#-----------------------------
# Output files
#-----------------------------
samplesheet_out <- "diffab_quantms_samplesheet_noBTC.csv"
matrix_out      <- "diann_report.pg_matrix_noBTC.tsv"
feature_out     <- "diann_report.pg_matrix_as_anno_noBTC.tsv"

#-----------------------------
# Read data
#-----------------------------
samples <- read_csv(samplesheet_file, show_col_types = FALSE)
matrix  <- read_tsv(matrix_file, show_col_types = FALSE)

#-----------------------------
# Remove BTC samples
#-----------------------------
samples <- samples[samples$seq_batch != "BTC", ]

# Samples to keep (must match matrix column names exactly)
keep_samples <- samples$sample

# Metadata columns at start of DIA-NN matrix
metadata_cols <- c(
  "Protein.Group",
  "Protein.Ids",
  "Protein.Names",
  "Genes",
  "First.Protein.Description"
)

# Keep only metadata + remaining sample columns
matrix <- matrix[, c(metadata_cols, keep_samples)]

#-----------------------------
# Feature annotation file
#-----------------------------
feature_anno <- matrix[, metadata_cols]

#-----------------------------
# Write outputs
#-----------------------------
write_csv(samples, samplesheet_out)

write_tsv(matrix, matrix_out)

write_tsv(feature_anno, feature_out)

#-----------------------------
# QC
#-----------------------------
cat("Remaining samples:", nrow(samples), "\n")
cat("Protein matrix dimensions:", nrow(matrix), "proteins x", ncol(matrix) - length(metadata_cols), "samples\n")
cat("Feature annotation dimensions:", nrow(feature_anno), "proteins\n")





library(readr)

mat <- read_tsv("diann_report.pg_matrix_noBTC_clean.tsv")

dim(mat)

colnames(mat)[1:10]

summary(as.numeric(unlist(mat[,6:ncol(mat)])))

sum(is.na(as.matrix(mat[,6:ncol(mat)])))


colSums(!is.na(mat))
which(sapply(mat[,6:ncol(mat)], function(x) all(is.na(x))))

samples <- read.csv("diffab_quantms_samplesheet_noBTC.csv")

setdiff(samples$sample, colnames(mat))

samples <- read.csv("diffab_quantms_samplesheet_noBTC.csv")

setdiff(samples$sample, colnames(mat))

anno <- read.delim("diann_report.pg_matrix_as_anno_noBTC.tsv")

nrow(anno)

sum(duplicated(anno$Protein.Group))

sum(anno$Protein.Group %in% mat$Protein.Group)


which(sapply(mat[,6:ncol(mat)], function(x) all(is.na(x))))



#-----------------------------
# Input files
#-----------------------------
samplesheet_file <- "diffab_quantms_samplesheet_batch1.csv"
mat_file      <- "diann_report.pg_matrix.tsv"

#-----------------------------
# Output files
#-----------------------------
sample_out <- "diffab_quantms_samplesheet_noBTC_clean.csv"
mat_out      <- "diann_report.pg_matrix_noBTC_clean.tsv"
feat_out     <- "diann_report.pg_matrix_as_anno_noBTC_clean.tsv"

#-----------------------------
# Read data
#-----------------------------
samples <- read_csv(samplesheet_file, show_col_types = FALSE)
mat  <- read_tsv(mat_file, show_col_types = FALSE)

#-----------------------------
# Remove BTC samples
#-----------------------------

bad_samples <- c(
  "CASE-NEUBK117YXL-5944-P_B09_profile.mzML",
  "CASE-NEUFH122WN7-5930-P_B08_profile.mzML"
)

samples <- samples[!samples$sample %in% bad_samples, ]
mat <- mat[, !colnames(mat) %in% bad_samples]


samples <- samples[samples$seq_batch != "BTC", ]

# Samples to keep (must match matrix column names exactly)
keep_samples <- samples$sample

# Metadata columns at start of DIA-NN matrix
metadata_cols <- c(
  "Protein.Group",
  "Protein.Ids",
  "Protein.Names",
  "Genes",
  "First.Protein.Description"
)

# Keep only metadata + remaining sample columns
mat <- mat[, c(metadata_cols, keep_samples)]

#-----------------------------
# Feature annotation file
#-----------------------------
feat_anno <- mat[, metadata_cols]

#-----------------------------
# Write outputs
#-----------------------------
write_csv(samples, sample_out)

write_tsv(mat, mat_out)

write_tsv(feat_anno, feature_out)













library(readr)

mat <- read_tsv("diann_report.pg_matrix_noBTC_clean.tsv", show_col_types = FALSE)

feature_metadata <- mat[, c(
  "Protein.Group",
  "Protein.Ids",
  "Protein.Names",
  "Genes",
  "First.Protein.Description"
)]

write_tsv(
  feature_metadata,
  "diann_report.pg_matrix_noBTC_feature_metadata_clean.tsv"
)
