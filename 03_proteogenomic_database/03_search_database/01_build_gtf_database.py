"""Build the gffutils database named in config/workflow.publication.v5.toml ([common] gtf_db).

Usage: python 01_build_gtf_database.py [GTF] [DB]
  GTF defaults to $GENCODE_GTF (GENCODE v46 Homo_sapiens_GRCh38_46.gtf; not in the repository)
  DB  defaults to 03_proteogenomic_database/data/gencode_v46.gtf.db
"""
import os
import sys
from pathlib import Path

import gffutils

PROJECT_DIR = Path(__file__).resolve().parents[1]
gtf_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "GENCODE_GTF", "/path/to/references/GRCh38/gencode_v46/gencode/Homo_sapiens_GRCh38_46.gtf")
db_file = Path(sys.argv[2]) if len(sys.argv) > 2 else PROJECT_DIR / "data" / "gencode_v46.gtf.db"
if not Path(gtf_file).is_file():
    sys.exit(f"GTF not found: {gtf_file}. Pass it as the first argument or set GENCODE_GTF.")
db_file.parent.mkdir(parents=True, exist_ok=True)
db_file = str(db_file)

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
