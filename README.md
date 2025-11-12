# FAIRe2ENA

Convert FAIRe-formatted metadata to ENA (European Nucleotide Archive) XML format for submission.

## Overview

This tool automates the conversion of *sample* metadata from the [FAIRe](https://fair-edna.github.io/) (Findable, Accessible, Interoperable, Reusable) standard to ENA's XML submission format, specifically targeting the ERC000024 (GSC MIxS water) checklist.

I am currently working on the same for the *run* metadata.

## Installation

### Requirements

```bash
pip install pandas openpyxl
```

## Usage

### Command Line Interface

```bash
python faire2ena_sample.py \
  -i <input_excel_file> \
  -c <center_name> \
  -o <output_xml_file>
```

### Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--input_file` | `-i` | Path to FAIRe-formatted Excel file | Yes |
| `--center_name` | `-c` | Name of the sequencing center | Yes |
| `--output_file` | `-o` | Output XML filename | Yes |

**Note:** The project name is now automatically extracted from the `projectMetadata` sheet in the Excel file (from the `project_id` term).

### Example

```bash
python faire2ena_sample.py \
  -i rowley_shoals_metadata.xlsx \
  -c "OceanOmics" \
  -o ena_samples.xml
```

## Input Format

The tool expects an Excel file with two sheets:

1. **`projectMetadata`** - Contains project-level information including `project_id`
2. **`sampleMetadata`** - Starting at row 3, contains FAIRe-formatted sample data

### Required Fields

- `eventDate` - Collection date (ISO 8601 format)
- `decimalLatitude` - Latitude in decimal degrees
- `decimalLongitude` - Longitude in decimal degrees
- `geo_loc_name` - Geographic location name
- `env_broad_scale` - Broad environmental context (with ENVO terms)
- `env_local_scale` - Local environmental context
- `env_medium` - Environmental medium (with ENVO terms)
- `minimumDepthInMeters` - Sampling depth

### Optional Fields

The tool supports mapping for 50+ optional fields including:
- Water chemistry (salinity, pH, dissolved oxygen, nutrients)
- Physical parameters (temperature, turbidity, conductivity)
- Sample collection details (device, method, volume)
- Sample processing (storage, extraction methods)

See the [Field Mapping](#field-mapping) section for complete details.

## Output Format

The tool generates an ENA-compliant XML file structured as:

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
        <VALUE>1.0</VALUE>
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

You can then submit that XML to ENA via curl - see the [ENA manual](https://ena-docs.readthedocs.io/en/latest/submit/general-guide/programmatic.html).

Example (note the use of wwwdev, the test server):

```bash
curl -u 'your_secret_ENI_email@office.com':'please_dont_steal_my_password_i_WILL_cry' \
  -F "SUBMISSION=@submission.xml" \
  -F "SAMPLE=@ena_submission.xml" \
  https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit
```

## Field Mapping

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

The tool automatically validates that all mandatory ENA fields are present. If any are missing, default values are applied:

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

### Missing Mandatory Fields

If you see validation warnings, check that your FAIRe file contains:
1. Collection date in ISO 8601 format (YYYY-MM-DD)
2. Geographic coordinates in decimal degrees
3. ENVO ontology terms for environmental contexts
4. Depth measurements in meters

The tool will apply sensible defaults for OceanOmics samples if these are missing.

### Invalid Collection Dates

Dates with invalid months or days (e.g., `2019-00-00`) will be automatically set to `'not provided'`. Ensure dates follow ISO 8601 format or use year-only precision if exact dates are unknown.

### Unit Handling

Fields with units are automatically combined:
- `samp_size: 1` + `samp_size_unit: L` → `amount or size of sample collected: 1 L`

Units are also added to specific fields via the `<UNITS>` XML tag:
- `depth` → units: `m`
- `geographic location (latitude/longitude)` → units: `DD` (decimal degrees)
- `amount or size of sample collected` → units: `L`

### Geographic Location Parsing

The `geo_loc_name` field is automatically parsed to extract the country/sea name:
- Input: `Indian Ocean: Rowley Shoals, Mermaid`
- Output: `Indian Ocean` (text before the first colon)

### Empty Values

Empty or `NaN` values are handled as follows:
- For control samples: set to `'missing: control sample'`
- For regular samples with missing mandatory fields: replaced with defaults
- Optional empty fields: omitted from the XML output
