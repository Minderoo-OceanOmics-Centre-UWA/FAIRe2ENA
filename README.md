# FAIRe2ENA

Convert FAIRe-formatted metadata to ENA (European Nucleotide Archive) XML format for submission.

## Overview

This toolset automates the conversion of metadata from the [FAIRe](https://fair-edna.github.io/) (Findable, Accessible, Interoperable, Reusable) standard to ENA's XML submission format.

The toolset consists of two scripts:
1. **`faire2ena_sample.py`** - Converts sample metadata to ENA SAMPLE XML (ERC000024 GSC MIxS water checklist)
2. **`faire2ena_run.py`** - Converts experiment/run metadata to ENA EXPERIMENT and RUN XML files


There is also a helper script written by Olivia Nguyen, `upload_reads_to_ena.py`, which uploads fastq.gz files to ENA.

## Installation

### Requirements

```bash
pip install pandas openpyxl
```

## Usage

### Workflow Overview

The typical ENA submission workflow is:

1. **Submit samples** using `faire2ena_sample.py`, generating a ENA receipt file
2. **Get sample accessions** from ENA receipt
3. **Upload FASTQ files** to ENA FTP using `upload_reads_to_ena.py`
4. **Submit experiments and runs** using `faire2ena_run.py` with the receipt file

### 1. Sample Submission (`faire2ena_sample.py`)

```bash
python faire2ena_sample.py \
  -i <input_excel_file> \
  -c <center_name> \
  -o <output_xml_file>
```

#### Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--input_file` | `-i` | Path to FAIRe-formatted Excel file | Yes |
| `--center_name` | `-c` | Name of the sequencing center | Yes |
| `--output_file` | `-o` | Output XML filename | Yes |

#### Example

```bash
python faire2ena_sample.py \
  -i rowley_shoals_metadata.xlsx \
  -c "OceanOmics" \
  -o ena_samples.xml
```

### 2. Read upload (`upload_reads_to_ena.py`)

This uploads fastq.gz files in the working directory to ENA.

```bash
python upload_reads.py 
  --host <host_name>
  --subdir <folder_name>
  --user <username>
  --passw <userpassword>
```

#### Arguments

| Argument | Description |
|----------|-------------|
| `--host` | URL of the FTP we're uploading to |
| `--subdir` | Subfolder on the FTP we're storing our files in |
| `--user` | Username for the FTP |
| `--passw` | Password for the FTP |


#### Example

```bash
python upload_reads.py
  --host "webin2.ebi.ac.uk"
  --subdir "reads"
  --user "webin12345"
  --passw "super_secret_ive_got_a_secret"
```




### 3. Experiment and Run Submission (`faire2ena_run.py`)

We then submit the `output_xml_file` to ENA via curl, which generates a receipt XML file. We then use `faire2ena_run.py` to write the experiment and run submission XML files.

```bash
python faire2ena_run.py \
  -i <input_excel_file> \
  -r <receipt_xml_file> \
  -s <study_accession> \
  -c <center_name> \
  -e <experiment_output_xml> \
  -o <run_output_xml>
```

#### Arguments

| Argument | Short | Description | Required | Default |
|----------|-------|-------------|----------|---------|
| `--input_file` | `-i` | Path to FAIRe-formatted Excel file | Yes | - |
| `--receipt_file` | `-r` | ENA sample submission receipt XML | Yes | - |
| `--study_accession` | `-s` | ENA study accession (e.g., PRJEB12345) | Yes | - |
| `--center_name` | `-c` | Name of the sequencing center | Yes | - |
| `--experiment_output` | `-e` | Output file for EXPERIMENT XML | No | `ena_experiments.xml` |
| `--run_output` | `-o` | Output file for RUN XML | No | `ena_runs.xml` |
| `--instrument_model` | `-m` | Sequencing instrument model | No | `Illumina NextSeq 2000` |

#### How it works

The script:
1. Parses the ENA sample receipt XML to extract sample alias → accession mappings (e.g., `RS19_C13_A_2` → `ERS32025180`)
2. Reads experiment/run metadata from the `experimentRunMetadata` sheet
3. Matches each library/run to its corresponding sample accession
4. Generates two separate XML files:
   - **EXPERIMENT XML**: Contains library preparation metadata (library strategy, source, selection, platform)
   - **RUN XML**: Contains sequencing run metadata (FASTQ filenames, MD5 checksums)

Each experiment is linked to a sample via the sample accession, and each run is linked to its experiment.

#### Example

```bash
# After receiving sample_receipt.xml from ENA
python faire2ena_run.py \
  -i rowley_shoals_metadata.xlsx \
  -r sample_receipt.xml \
  -s PRJEB12345 \
  -c "OceanOmics" \
  -e ena_experiments.xml \
  -o ena_runs.xml \
  -m "Illumina NovaSeq 6000"
```

#### Output

The script will generate two files and print summary information:

```
INFO: Loaded 245 sample accessions from receipt
INFO: Generated EXPERIMENT XML with 245 experiments -> ena_experiments.xml
INFO: Generated RUN XML with 245 runs -> ena_runs.xml
```

If any samples are missing from the receipt, you'll see warnings:

```
WARNING: Skipped 3 samples without accessions:
  - RS19_C20_E_2
  - RS19_M12_C_2
  - RS19_M15_A_1
```

## Input Format

Boh scripts expects an Excel file with multiple sheets:

1. **`projectMetadata`** - Contains project-level information including `project_id`
2. **`sampleMetadata`** - Starting at row 3, contains FAIRe-formatted sample data
3. **`experimentRunMetadata`** - Starting at row 3, contains sequencing run and library preparation data

### Sample Metadata Sheet (`sampleMetadata`)

#### Required Fields

- `eventDate` - Collection date (ISO 8601 format)
- `decimalLatitude` - Latitude in decimal degrees
- `decimalLongitude` - Longitude in decimal degrees
- `geo_loc_name` - Geographic location name
- `env_broad_scale` - Broad environmental context (with ENVO terms)
- `env_local_scale` - Local environmental context
- `env_medium` - Environmental medium (with ENVO terms)
- `minimumDepthInMeters` - Sampling depth

#### Optional Fields

The tool supports mapping for 50+ optional fields including:
- Water chemistry (salinity, pH, dissolved oxygen, nutrients)
- Physical parameters (temperature, turbidity, conductivity)
- Sample collection details (device, method, volume)
- Sample processing (storage, extraction methods)

See the [Field Mapping](#field-mapping) section for complete details.

### Experiment/Run Metadata Sheet (`experimentRunMetadata`)

#### Required Fields

- `samp_name` - Sample name (must match `samp_name` from `sampleMetadata`)
- `lib_id` - Library identifier
- `filename` - Forward read FASTQ filename
- `filename2` - Reverse read FASTQ filename
- `checksum_filename` - MD5 checksum for forward read
- `checksum_filename2` - MD5 checksum for reverse read

#### Optional Fields

- `assay_name` - Assay or marker name
- `pcr_plate_id` - PCR plate identifier
- `seq_run_id` - Sequencing run identifier
- `lib_conc` - Library concentration value
- `lib_conc_unit` - Library concentration unit
- `lib_conc_meth` - Library quantification method
- `phix_perc` - PhiX spike-in percentage
- `mid_forward` - Forward index/barcode
- `mid_reverse` - Reverse index/barcode
- `input_read_count` - Number of raw reads
- `output_read_count` - Number of processed reads
- `output_otu_num` - Number of OTUs/ASVs
- `otu_num_tax_assigned` - Number of taxonomically assigned OTUs

## Output Format

### Sample XML (`faire2ena_sample.py`)

The tool generates an ENA-compliant SAMPLE XML file structured as:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SAMPLE_SET>
  <SAMPLE alias="RS19_RS1_1_A" center_name="OceanOmics">
    <SAMPLE_NAME>
      <TAXON_ID>408172</TAXON_ID>
    </SAMPLE_NAME>
    <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>amount or size of sample collected</TAG>
        <VALUE>1.0 L</VALUE>
        <UNITS>L</UNITS>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>broad-scale environmental context</TAG>
        <VALUE>ocean biome [ENVO:01000048]</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>collection date</TAG>
        <VALUE>2019-10-16</VALUE>
      </SAMPLE_ATTRIBUTE>
  <!-- More samples... -->
</SAMPLE_SET>
```

### Experiment XML (`faire2ena_run.py`)

The tool generates an ENA-compliant EXPERIMENT XML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EXPERIMENT_SET>
  <EXPERIMENT alias="RS19_C13_A" center_name="OceanOmics">
    <TITLE>RS19_C13_A</TITLE>
    <STUDY_REF accession="PRJEB12345"/>
    <DESIGN>
      <DESIGN_DESCRIPTION>eDNA metabarcoding</DESIGN_DESCRIPTION>
      <SAMPLE_DESCRIPTOR accession="ERS32025180"/>
      <LIBRARY_DESCRIPTOR>
        <LIBRARY_NAME>RS19_C13_A</LIBRARY_NAME>
        <LIBRARY_STRATEGY>AMPLICON</LIBRARY_STRATEGY>
        <LIBRARY_SOURCE>METAGENOMIC</LIBRARY_SOURCE>
        <LIBRARY_SELECTION>PCR</LIBRARY_SELECTION>
        <LIBRARY_LAYOUT>
          <PAIRED/>
        </LIBRARY_LAYOUT>
      </LIBRARY_DESCRIPTOR>
    </DESIGN>
    <PLATFORM>
      <ILLUMINA>
        <INSTRUMENT_MODEL>Illumina NovaSeq 6000</INSTRUMENT_MODEL>
      </ILLUMINA>
    </PLATFORM>
  </EXPERIMENT>
  <!-- More experiments... -->
</EXPERIMENT_SET>
```

### Run XML (`faire2ena_run.py`)

The tool generates an ENA-compliant RUN XML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<RUN_SET>
  <RUN alias="RS19_C13_A_run" center_name="OceanOmics">
    <EXPERIMENT_REF refname="RS19_C13_A"/>
    <DATA_BLOCK>
      <FILES>
        <FILE filename="RS19_C13_A.R1.fq.gz" filetype="fastq" 
              checksum_method="MD5" checksum="674097d23b8497452c223a933325cbf3"/>
        <FILE filename="RS19_C13_A.R2.fq.gz" filetype="fastq" 
              checksum_method="MD5" checksum="0f4a6a2dc433b8da4269b864d8d9a314"/>
      </FILES>
    </DATA_BLOCK>
  </RUN>
  <!-- More runs... -->
</RUN_SET>
```

### Submission to ENA

You can submit these XML files to ENA via curl - see the [ENA manual](https://ena-docs.readthedocs.io/en/latest/submit/general-guide/programmatic.html).

#### Sample Submission Example

```bash
curl -u 'your_email@office.com':'please_dont_steal_my_password_I_WILL_cry' \
  -F "SUBMISSION=@submission.xml" \
  -F "SAMPLE=@ena_samples.xml" \
  https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit
```

This will return a receipt XML file with sample accessions (ERS...).

#### Experiment and Run Submission Example

```bash
curl -u 'your_email@office.com':'your_password' \
  -F "SUBMISSION=@submission.xml" \
  -F "EXPERIMENT=@ena_experiments.xml" \
  -F "RUN=@ena_runs.xml" \
  https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit
```

**Note:** Use `wwwdev.ebi.ac.uk` for testing. For production submissions, use `www.ebi.ac.uk`.

## Field Mapping


The FAIRe fields differ a bit from the ENA checklist fields. Here's the mapping.

### Core Metadata

| FAIRe Field | ENA Field | Mandatory |
|-------------|-----------|-----------|
| `materialSampleID` | `source material identifiers` | Optional |
| `eventDate` | `collection date` | **Yes** |
| `decimalLatitude` | `geographic location (latitude)` | **Yes** |
| `decimalLongitude` | `geographic location (longitude)` | **Yes** |
| `geo_loc_name` | `geographic location (country and/or sea)` | **Yes** |
| `env_broad_scale` | `broad-scale environmental context` | **Yes** |
| `env_local_scale` | `local environmental context` | **Yes** |
| `env_medium` | `environmental medium` | **Yes** |
| `minimumDepthInMeters` | `depth` | **Yes** |

### Sample Collection

| FAIRe Field | ENA Field |
|-------------|-----------|
| `samp_collect_device` | `sample collection device` |
| `samp_collect_method` | `sample collection method` |
| `samp_size` + `samp_size_unit` | `amount or size of sample collected` |
| `samp_store_temp` | `sample storage temperature` |
| `samp_store_loc` | `sample storage location` |
| `samp_store_dur` | `sample storage duration` |
| `samp_category` | `control_sample` |

### Environmental Measurements

| FAIRe Field | ENA Field |
|-------------|-----------|
| `temp` | `temperature` |
| `salinity` | `salinity` |
| `ph` | `ph` |
| `diss_oxygen` | `dissolved oxygen` |
| `chlorophyll` | `chlorophyll` |
| `turbidity` | `turbidity` |

### Water Chemistry

| FAIRe Field | ENA Field |
|-------------|-----------|
| `nitrate` | `nitrate` |
| `nitrite` | `nitrite` |
| `diss_org_carb` | `dissolved organic carbon` |
| `diss_inorg_carb` | `dissolved inorganic carbon` |
| `tot_nitro` | `total nitrogen concentration` |

[See full mapping in source code]

## Validation and Error Handling

### Mandatory Field Validation

`faire2end_sample.py` validates that all mandatory ENA fields are present. If any are missing, default values are applied:

```
WARNING: Sample name RS19_RS1_1_A missing mandatory field 'depth', setting to default '0'
```

**Default Values:**
- `env_local_scale`: `marine pelagic zone [ENVO:00000208]`
- `minimumDepthInMeters`: `0` (most OceanOmics samples are surface)

### Date Validation

Collection dates are validated against ENA's required pattern. Invalid dates (such as `2019-00-00`) are automatically replaced:

```
WARNING: Sample name RS19_RS1_1_A has invalid date 2019-00-00T00:00:00. Replacing with 'not provided'.
```

**Valid date formats:**
- Full date: `2019-10-16`
- Year-month: `2019-10`
- Year only: `2019`
- Date with time: `2019-10-16T00:00:00`
- Missing values: `not provided`, `not collected`

### Control Samples

Control samples (where `samp_category` is not `'sample'`) are handled specially:
- `control_sample` field is set to `TRUE`
- Missing mandatory fields are set to `'missing: control sample'`
- Optional fields with no data are omitted from the XML

## Taxon ID

The default taxon ID is set to `408172` (marine metagenome). Modify this in the code if working with different organisms:

```python
process_faire_df(df, args.output_file, project_name,
                 taxon_id='YOUR_TAXON_ID',
                 center_name=args.center_name)
```

## Troubleshooting

### Sample Submission Issues

#### Missing Mandatory Fields

If you see validation warnings, check that your FAIRe file contains:
1. Collection date in ISO 8601 format (YYYY-MM-DD)
2. Geographic coordinates in decimal degrees
3. ENVO ontology terms for environmental contexts
4. Depth measurements in meters

The tool will apply sensible defaults for OceanOmics samples if these are missing.

#### Invalid Collection Dates

Dates with invalid months or days (e.g., `2019-00-00`) will be automatically set to `'not provided'`. Ensure dates follow ISO 8601 format or use year-only precision if exact dates are unknown.

#### Unit Handling

Units also added to specific fields via the `<UNITS>` XML tag, there's a hardcoded look-up table which you may need to change.

- `depth` → units: `m`
- `geographic location (latitude/longitude)` → units: `DD` (decimal degrees)
- `amount or size of sample collected` → units: `L`

#### Geographic Location Parsing

The `geo_loc_name` field is automatically parsed to extract the country/sea name:
- Input: `Indian Ocean: Rowley Shoals, Mermaid`
- Output: `Indian Ocean` (text before the first colon)

#### Empty Values

Empty or `NaN` values are handled as follows:
- For control samples: set to `'missing: control sample'`
- For regular samples with missing mandatory fields: replaced with defaults
- Optional empty fields: omitted from the XML output

### Experiment/Run Submission Issues

#### Missing Sample Accessions

If samples are skipped during run submission, check:
1. The receipt XML file contains all sample accessions
2. The `samp_name` values match exactly between `sampleMetadata` and `experimentRunMetadata` sheets
3. All samples were successfully submitted in the first step

The script will warn you about skipped samples:
```
WARNING: Skipped 3 samples without accessions:
  - RS19_C20_E_2
  - RS19_M12_C_2
```

#### Missing FASTQ Files or Checksums

Ensure your `experimentRunMetadata` sheet contains:
- `filename` and `filename2` - full FASTQ filenames with extensions
- `checksum_filename` and `checksum_filename2` - valid MD5 checksums

You can generate MD5 checksums with:
```bash
md5sum your_file.fastq.gz
```

#### Study Accession

Make sure you have a valid ENA study accession (PRJEB...) before submitting experiments and runs. You need to create a study separately through the ENA Webin portal or API.
