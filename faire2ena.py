# First, we pull out the sample metadata nad map to ERC000024

from typing import Dict, List, Tuple
from datetime import datetime
from argparse import ArgumentParser
import pandas as pd

# Mapping dictionary: FAIRe field -> ENA field
FAIRE_TO_ENA_MAPPING = {
    'materialSampleID': 'source_material_identifiers',
    
    # Collection date and location (MANDATORY)
    'eventDate': 'collection_date',
    'decimalLatitude': 'geographic_location_latitude',
    'decimalLongitude': 'geographic_location_longitude',
    'geo_loc_name': 'geographic_location_region_and_locality',
    
    # Environmental context (MANDATORY)
    'env_broad_scale': 'broadscale_environmental_context',
    'env_local_scale': 'local_environmental_context',
    'env_medium': 'environmental_medium',
    
    # Depth (MANDATORY for water samples)
    'minimumDepthInMeters': 'depth',  
    'maximumDepthInMeters': None,  # we generally treat minimum and maximum identically
    
    'samp_collect_device': 'sample_collection_device',
    'samp_collect_method': 'sample_collection_method',
    'samp_size': 'amount_or_size_of_sample_collected',
    'samp_size_unit': None,  # Combined with samp_size
    'samp_store_temp': 'sample_storage_temperature',
    'samp_store_loc': 'sample_storage_location',
    'samp_store_dur': 'sample_storage_duration',
    'samp_category': 'control_sample',
    
    'size_frac_low': 'sizefraction_lower_threshold',
    'size_frac': 'sizefraction_upper_threshold',
    
    'temp': 'temperature',
    'salinity': 'salinity',
    'ph': 'ph',
    'tot_depth_water_col': 'total_depth_of_water_column',
    'elev': 'elevation',
    
    'diss_oxygen': 'dissolved_oxygen',
    'nitrate': 'nitrate',
    'nitrite': 'nitrite',
    'diss_inorg_carb': 'dissolved_inorganic_carbon',
    'diss_inorg_nitro': 'dissolved_inorganic_nitrogen',
    'diss_org_carb': 'dissolved_organic_carbon',
    'diss_org_nitro': 'dissolved_organic_nitrogen',
    'tot_diss_nitro': 'total_dissolved_nitrogen',
    'tot_inorg_nitro': 'total_inorganic_nitrogen',
    'tot_nitro': 'total_nitrogen_concentration',
    'tot_part_carb': 'total_particulate_carbon',
    'tot_org_carb': 'total_organic_carbon',
    'tot_nitro_content': 'total_nitrogen_content',
    'part_org_carb': 'particulate_organic_carbon',
    'part_org_nitro': 'particulate_organic_nitrogen',
    'org_carb': 'organic_carbon',
    'org_matter': 'organic_matter',
    'org_nitro': 'organic_nitrogen',
    
    'chlorophyll': 'chlorophyll',
    'light_intensity': 'light_intensity',
    'suspend_part_matter': 'suspended_particulate_matter',
    'tidal_stage': 'tidal_stage',
    'turbidity': 'turbidity',
    'water_current': 'water_current',
    
    'samp_mat_process': 'sample_material_processing',
    'samp_vol_we_dna_ext': 'sample_volume_or_weight_for_dna_extraction',
    'nucl_acid_ext': 'nucleic_acid_extraction',
    'nucl_acid_ext_kit': None,  # Can be combined with nucl_acid_ext
    
    'neg_cont_type': 'negative_control_type',
    'pos_cont_type': 'positive_control_type',
    
    # OceanOmics-specific fields - TODO; decide?
    'biological_rep': 'replicate_id',  # NOT a FAIRe term - an OceanOmics term
    'site_id': None,  # Not directly mapped to ENA
    'tube_id': None,  # Not directly mapped to ENA
}


def combine_value_with_unit(value: str, unit: str) -> str:
    """
    Combine a measurement value with its unit.
    """
    if pd.isna(value) or pd.isna(unit):
        return 'Unknown'
    if value and unit:
        return f"{value} {unit}"
    elif value:
        return f"{value}"
    return ""


def convert_faire_to_ena(faire_data: Dict[str, str], project_name: str) -> Dict[str, str]:
    """
    Convert FAIRe metadata dictionary to ENA format.
    
    Args:
        faire_data (dict): Dictionary with FAIRe metadata fields
        project_name (str): Project name (required by ENA if not in faire_data)
        
    Returns:
        dict: Dictionary with ENA field names and values
    """
    ena_data = {}
    
    if project_name:
        ena_data['project_name'] = project_name
    
    for faire_field, ena_field in FAIRE_TO_ENA_MAPPING.items():
        if ena_field and faire_field in faire_data:
            value = faire_data.get(faire_field, '')
            if pd.isna(value):
                value = 'Unknown'
            elif value:
                ena_data[ena_field] = value
    
    # Special handling for combined fields
    
    min_depth = faire_data.get('minimumDepthInMeters', '')
    max_depth = faire_data.get('maximumDepthInMeters', '')
    # OceanOmics usually sets these to the same
    if min_depth or max_depth:
        #ena_data['depth'] = parse_depth(min_depth, max_depth)
        ena_data['depth'] = min_depth

    
    samp_size = faire_data.get('samp_size', '')
    samp_size_unit = faire_data.get('samp_size_unit', '')
    if samp_size:
        ena_data['amount_or_size_of_sample_collected'] = combine_value_with_unit(
            samp_size, samp_size_unit
        )

    if ena_data['control_sample'] == 'sample':
        ena_data['control_sample'] = 'FALSE'
    else:
        ena_data['control_sample'] = 'TRUE'
    
    dna_vol = faire_data.get('samp_vol_we_dna_ext', '')
    dna_vol_unit = faire_data.get('samp_vol_we_dna_ext_unit', '')
    if dna_vol:
        ena_data['sample_volume_or_weight_for_dna_extraction'] = combine_value_with_unit(
            dna_vol, dna_vol_unit
        )
    
    geo_loc_name = faire_data.get('geo_loc_name', '')
    if not pd.isna(geo_loc_name) and geo_loc_name:
        # turn Indian Ocean: Rowley Shoals, Mermaid into Indian Ocean
        ena_data['geographic_location_country_andor_sea'] = geo_loc_name.split(':')[0].strip()
    
    nucl_ext = faire_data.get('nucl_acid_ext', '')
    nucl_ext_kit = faire_data.get('nucl_acid_ext_kit', '')
    if pd.isna(nucl_ext):
        ena_data['nucleic_acid_extraction'] = 'Unknown'
    elif nucl_ext and nucl_ext_kit:
        ena_data['nucleic_acid_extraction'] = f"{nucl_ext} ({nucl_ext_kit})"
    elif nucl_ext:
        ena_data['nucleic_acid_extraction'] = nucl_ext
    
    if 'replicate_id' in ena_data: 
        ena_data['replicate_id'] = str(int(ena_data['replicate_id']))
    
    unit_mappings = [
        ('diss_inorg_carb', 'diss_inorg_carb_unit', 'dissolved_inorganic_carbon'),
        ('diss_inorg_nitro', 'diss_inorg_nitro_unit', 'dissolved_inorganic_nitrogen'),
        ('diss_org_carb', 'diss_org_carb_unit', 'dissolved_organic_carbon'),
        ('diss_org_nitro', 'diss_org_nitro_unit', 'dissolved_organic_nitrogen'),
        ('diss_oxygen', 'diss_oxygen_unit', 'dissolved_oxygen'),
        ('nitrate', 'nitrate_unit', 'nitrate'),
        ('nitrite', 'nitrite_unit', 'nitrite'),
    ]
    
    for value_field, unit_field, ena_field in unit_mappings:
        value = faire_data.get(value_field, '')
        unit = faire_data.get(unit_field, '')
        if pd.isna(value):
            value = 'Unknown'
        elif value:
            ena_data[ena_field] = combine_value_with_unit(value, unit)
    
    return ena_data


def validate_mandatory_fields(ena_data: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that all mandatory ENA fields are present.
    
    Args:
        ena_data (dict): Dictionary with ENA metadata
        
    Returns:
        tuple: (bool, list) - (is_valid, missing_fields)
    """
    mandatory_fields = [
        'project_name',
        'collection_date',
        'geographic_location_latitude',
        'geographic_location_longitude',
        'geographic_location_country_andor_sea',
        'broadscale_environmental_context',
        'local_environmental_context',
        'environmental_medium',
        'depth'
    ]
    
    missing = [field for field in mandatory_fields if field not in ena_data or not ena_data[field]]
    return len(missing) == 0, missing


def generate_ena_xml(ena_data: Dict[str, str], sample_alias: str, 
                     taxon_id: str = "32644", center_name: str = "YOUR_CENTER") -> str:
    """
    Generate ENA XML string from metadata dictionary.
    
    Args:
        ena_data (dict): Dictionary with ENA metadata
        sample_alias (str): Unique identifier for the sample
        taxon_id (str): NCBI Taxonomy ID (default: 32644 for unidentified)
        center_name (str): Your center/institution name
        
    Returns:
        str: XML string formatted for ENA submission
    """
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<SAMPLE_SET>')
    xml_parts.append(f'  <SAMPLE alias="{sample_alias}" center_name="{center_name}">')
    xml_parts.append('    <SAMPLE_NAME>')
    xml_parts.append(f'      <TAXON_ID>{taxon_id}</TAXON_ID>')
    xml_parts.append('    </SAMPLE_NAME>')
    xml_parts.append('    <SAMPLE_ATTRIBUTES>')
    
    for field_name, value in sorted(ena_data.items()):
        if value and value != 'Unknown':  # Only include non-empty values
            # Escape XML special characters
            # TODO - do we skip Unknowns? 
            value_escaped = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append('      <SAMPLE_ATTRIBUTE>')
            xml_parts.append(f'        <TAG>{field_name}</TAG>')
            xml_parts.append(f'        <VALUE>{value_escaped}</VALUE>')
            xml_parts.append('      </SAMPLE_ATTRIBUTE>')
    
    xml_parts.append('       <SAMPLE_ATTRIBUTE>')
    xml_parts.append('         <TAG>ENA-CHECKLIST</TAG>')
    xml_parts.append('         <VALUE>ERC000024</VALUE>')
    xml_parts.append('       </SAMPLE_ATTRIBUTE>')
    xml_parts.append('    </SAMPLE_ATTRIBUTES>')
    xml_parts.append('  </SAMPLE>')
    xml_parts.append('</SAMPLE_SET>')
    
    return '\n'.join(xml_parts)


def process_faire_df(input_df: pd.DataFrame, output_file: str, project_name: str,
        taxon_id: str, center_name: str):
    samples_xml = []
         
    list_of_dicts = input_df.to_dict(orient = 'records')

    for row in list_of_dicts:
        ena_data = convert_faire_to_ena(row, project_name)
        
        is_valid, missing = validate_mandatory_fields(ena_data)
        sample_name = row.get('samp_name', 'unknown')
        
        if not is_valid:
            print(f"WARNING: Sample {sample_name} missing mandatory fields: {missing}")
        
        sample_xml = generate_ena_xml(
            ena_data, 
            sample_name,
            taxon_id,
            center_name
        )
        
        sample_lines = sample_xml.split('\n')[2:-1]  # Skip header and closing tag
        samples_xml.extend(sample_lines)
    
    # Write combined XML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<SAMPLE_SET>\n')
        f.write('\n'.join(samples_xml))
        f.write('\n</SAMPLE_SET>\n')
    
    print(f"Generated ENA XML with {len(samples_xml)} samples -> {output_file}")


if __name__ == "__main__":
    parser = ArgumentParser(prog = 'FAIRe2ENA', description = 'Writes a sample-level XML file for submission to ENA')

    parser.add_argument('-i', '--input_file', help='Path of the FAIRe-formatted Excel file', required = True)
    parser.add_argument('-n', '--name', help = 'Name of the project for ENA submission', required = True)
    parser.add_argument('-c', '--center_name', help = 'Name of the sequencing centre for ENA submission', required = True)
    parser.add_argument('-o', '--output_file', help = 'Name of the output file to submit to ENA', required = True)

    args = parser.parse_args()

    df = pd.read_excel(args.input_file, sheet_name = 'sampleMetadata', skiprows = 2)

    process_faire_df(df, args.output_file, args.name, taxon_id = '408172', center_name = args.center_name)
