import gffutils

gtf_file = "/home/kcoetzer/nf/nf_references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46.gtf"
db_file = "gencode_v46.gtf.db"

# Create the database
db = gffutils.create_db(
    gtf_file,
    dbfn=db_file,
    force=True,        # overwrite if exists
    keep_order=True,
    merge_strategy="merge",
    sort_attribute_values=True
)

print(f"Database created: {db_file}")
