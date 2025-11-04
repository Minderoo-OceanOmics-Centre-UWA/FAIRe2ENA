# FAIRe2ENA

Convert FAIRe-formatted metadata to ENA (European Nucleotide Archive) XML format for submission.

## Overview

This tool automates the conversion of sample metadata from the FAIRe (Findable, Accessible, Interoperable, Reusable) standard to ENA's XML submission format, specifically targeting the ERC000024 (GSC MIxS water) checklist.

## Installation

### Requirements

```bash
pip install pandas openpyxl
```

## Usage

### Command Line Interface

```bash
python faire2ena.py \
  -i <input_excel_file> \
  -a <assay_name> \
  -n <project_name> \
  -c <center_name> \
  -o <output_xml_file>
```

### Arguments

| Argument | Short | Description | Required |
|----------|-------|-------------|----------|
| `--input_file` | `-i` | Path to FAIRe-formatted Excel file | Yes |
| `--assay` | `-a` | Name of the sequencing assay used | Yes |
| `--name` | `-n` | Project name for ENA submission | Yes |
| `--center_name` | `-c` | Name of the sequencing center | Yes |
| `--output_file` | `-o` | Output XML filename | Yes |

### Example

```bash
python faire2ena.py \
  -i rowley_shoals_metadata.xlsx \
  -a "MiFish-U" \
  -n "Rowley Shoals Marine eDNA Survey" \
  -c "OceanOmics" \
  -o ena_samples.xml
```

## Input Format

The tool expects an Excel file with a `sampleMetadata` sheet (starting at row 3) containing FAIRe-formatted columns:

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
  <SAMPLE alias="RS19_RS1_1_A" center_name="blu">
    <SAMPLE_NAME>
      <TAXON_ID>408172</TAXON_ID>
    </SAMPLE_NAME>
    <SAMPLE_ATTRIBUTES>
      <SAMPLE_ATTRIBUTE>
        <TAG>amount_or_size_of_sample_collected</TAG>
        <VALUE>1.0 L</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>broadscale_environmental_context</TAG>
        <VALUE>ocean biome [ENVO:01000048]</VALUE>
      </SAMPLE_ATTRIBUTE>
      <SAMPLE_ATTRIBUTE>
        <TAG>collection_date</TAG>
        <VALUE>2019-10-16T00:00:00</VALUE>
      </SAMPLE_ATTRIBUTE>
  <!-- More samples... -->
</SAMPLE_SET>
```

## Field Mapping

### Core Metadata

| FAIRe Field | ENA Field | Mandatory |
|-------------|-----------|-----------|
| `materialSampleID` | `source_material_identifiers` | Optional |
| `eventDate` | `collection_date` | **Yes** |
| `decimalLatitude` | `geographic_location_latitude` | **Yes** |
| `decimalLongitude` | `geographic_location_longitude` | **Yes** |
| `geo_loc_name` | `geographic_location_country_andor_sea` | **Yes** |
| `env_broad_scale` | `broadscale_environmental_context` | **Yes** |
| `env_local_scale` | `local_environmental_context` | **Yes** |
| `env_medium` | `environmental_medium` | **Yes** |
| `minimumDepthInMeters` | `depth` | **Yes** |

### Sample Collection

| FAIRe Field | ENA Field |
|-------------|-----------|
| `samp_collect_device` | `sample_collection_device` |
| `samp_collect_method` | `sample_collection_method` |
| `samp_size` + `samp_size_unit` | `amount_or_size_of_sample_collected` |
| `samp_store_temp` | `sample_storage_temperature` |
| `samp_store_loc` | `sample_storage_location` |
| `samp_store_dur` | `sample_storage_duration` |

### Environmental Measurements

| FAIRe Field | ENA Field |
|-------------|-----------|
| `temp` | `temperature` |
| `salinity` | `salinity` |
| `ph` | `ph` |
| `diss_oxygen` | `dissolved_oxygen` |
| `chlorophyll` | `chlorophyll` |
| `turbidity` | `turbidity` |

### Water Chemistry

| FAIRe Field | ENA Field |
|-------------|-----------|
| `nitrate` | `nitrate` |
| `nitrite` | `nitrite` |
| `diss_org_carb` | `dissolved_organic_carbon` |
| `diss_inorg_carb` | `dissolved_inorganic_carbon` |
| `tot_nitro` | `total_nitrogen_concentration` |

[See full mapping in source code]

## Validation

The tool automatically validates that all mandatory ENA fields are present. If any are missing, a warning is displayed:

```
WARNING: Sample RS19_RS1_1_A missing mandatory fields: ['depth', 'collection_date']
```

## Taxon ID

The default taxon ID is set to `408172` (marine metagenome). Modify this in the code if working with different organisms:

```python
process_faire_df(df, args.output_file, args.name, 
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

### Unit Handling

Fields with units are automatically combined:
- `samp_size: 1` + `samp_size_unit: L` → `amount_or_size_of_sample_collected: 1 L`

If units are missing, the tool uses "Unknown".

### Empty Values

Empty or `NaN` values are converted to "Unknown" for required fields.
