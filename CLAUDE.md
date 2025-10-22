# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MTBParser is a Python-based parser and FHIR mapper for Italian Molecular Tumor Board (MTB) clinical reports. It extracts structured clinical molecular data from unstructured text reports and converts them to HL7 FHIR R4 format for interoperability.

## Core Architecture

### Main Components

The codebase is organized around two primary classes in `mtb_parser.py`:

1. **MTBParser** (lines 60-270): Extracts structured data from free-text MTB reports
   - Uses regex patterns to identify and extract genomic variants, patient info, diagnoses, and therapeutic recommendations
   - Handles multiple variant notation formats (cDNA, protein changes, fusions)
   - Extracts tumor mutational burden (TMB) values
   - Supports both tabular and inline text formats

2. **FHIRMapper** (lines 272-547): Converts parsed MTB data to FHIR R4 resources
   - Creates FHIR Patient, Observation, and DiagnosticReport resources
   - Maps gene symbols to HGNC codes
   - Uses LOINC codes for genomic observations
   - Generates complete FHIR Bundles for interoperability

### Data Model

Six dataclasses define the domain model (lines 14-58):
- `Variant`: Genomic variants with gene, cDNA/protein changes, classification, VAF
- `Patient`: Demographics (ID, age, sex, birth date)
- `Diagnosis`: Clinical diagnosis, stage, histology
- `TherapeuticRecommendation`: Drug recommendations with evidence and rationale
- `MTBReport`: Complete parsed report containing all above entities

## Development Commands

### Running the Parser

Execute the main script with sample data:
```bash
python3 mtb_parser.py
```

The script includes a built-in test case that parses a sample MTB report and outputs both structured data and FHIR bundle.

### Testing the Parser

To test parsing your own reports:
```python
from mtb_parser import MTBParser, FHIRMapper

parser = MTBParser()
report = parser.parse_report(your_text_content)

fhir_mapper = FHIRMapper()
fhir_bundle = fhir_mapper.create_fhir_bundle(report)
```

### Dependencies

Required Python packages:
- `pandas`: For potential data manipulation (imported but not actively used)
- Standard library: `re`, `json`, `dataclasses`, `datetime`, `typing`

Install dependencies:
```bash
pip install pandas
```

## Key Implementation Details

### Variant Extraction Patterns

The parser handles multiple Italian MTB report formats:
- **Tabular format**: `Gene | cDNA | Protein | Classification | VAF%`
- **Inline mutations**: `EGFR L858R 45%`
- **Gene fusions**: `fusione ALK::EML4` or `riarrangiamento RET/PTC`
- **Classification terms**: Supports Italian (patogenetica, VUS) and English terminology

See `variant_patterns` (lines 65-75) and related extraction methods.

### FHIR Mapping Strategy

FHIR resources follow genomics reporting IG guidelines:
- **Patient**: Standard FHIR Patient resource with Italian date format conversion
- **Observation**: Uses LOINC codes for genetic variants (69548-6 for variant assessment)
- **Components**: Separate components for gene (48018-6), protein change (48005-3), DNA change (48004-6), VAF (81258-6)
- **DiagnosticReport**: Master genetic panel (81247-9) linking all observations
- **TMB**: Separate observation using LOINC 94076-7

### Drug and Gene Mappings

- **Targeted therapies**: Pre-defined regex patterns for common oncology drugs (lines 91-102)
- **Gene codes**: HGNC mappings for common cancer genes (lines 276-286)
- **Classification mapping**: Italian/English pathogenicity terms (lines 78-89)

## Working with This Codebase

### Adding Support for New Genes

Update the `gene_code_map` in `FHIRMapper.__init__()` (line 276):
```python
'GENE_SYMBOL': {'system': 'http://www.genenames.org', 'code': 'HGNC:XXXX'}
```

### Extending Variant Pattern Recognition

Add new regex patterns to `MTBParser.__init__()` in the `variant_patterns` list (line 65) or in the extraction methods like `extract_variants()` (line 154).

### Adding New Drug Classes

Extend `drug_patterns` in `MTBParser.__init__()` (line 91) with new therapeutic agent patterns.

### FHIR Resource Customization

Modify the resource creation methods in `FHIRMapper`:
- `create_patient_resource()` for Patient resources
- `create_variant_observation()` for genomic Observations
- `create_diagnostic_report()` for DiagnosticReport
- `create_fhir_bundle()` for the complete Bundle

## Italian Language Context

The parser is specifically designed for Italian MTB reports:
- Patient fields: "Età", "Sesso", "Diagnosi", "Data di nascita"
- Variant terms: "fusione", "riarrangiamento", "mutazione", "alterazione"
- Classification: "patogenetica", "variante a significato incerto"
- Date format: DD/MM/YYYY (converted to ISO for FHIR)

Maintain Italian regex patterns when extending functionality, but use English for code and FHIR resources.
