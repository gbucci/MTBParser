# MTBParser - Molecular Tumor Board Report Parser System

**Version 1.0.0** - Complete system for parsing, standardizing, and ensuring interoperability of clinical molecular data from Italian Molecular Tumor Board (MTB) reports.

## 🎯 Overview

MTBParser converts unstructured Italian MTB clinical text reports into internationally standardized formats (FHIR R4, GA4GH Phenopackets v2, OMOP CDM v5.4) to facilitate computational analysis and integration with clinical systems.

### Key Features

✅ **Multi-standard interoperability**: FHIR R4, GA4GH Phenopackets v2, OMOP CDM v5.4
✅ **Controlled vocabularies**: ICD-O-3, RxNorm, HGNC, SNOMED-CT, LOINC
✅ **Italian/English support**: Bilingual pattern matching
✅ **Advanced NLP**: Genomic variant extraction (HGVS, fusions, VAF)
✅ **Quality metrics**: Automated quality assessment and scoring
✅ **Multiple export formats**: JSON, CSV, FHIR Bundle, Phenopacket
✅ **Zero external dependencies**: Pure Python standard library

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/MTBParser.git
cd MTBParser

# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# No dependencies required for core functionality
# Optional dependencies in requirements.txt
```

---

## 🚀 Quick Start

### Basic Usage

```python
from core.mtb_parser import MTBParser

# Parse MTB report
parser = MTBParser()
report = parser.parse_report("""
    Paziente: 12345
    Età: 65 anni
    Sesso: M

    Diagnosi: Adenocarcinoma polmonare stadio IV

    Varianti:
    EGFR c.2573T>G p.Leu858Arg Pathogenic 45%
    ALK::EML4 fusion

    TMB: 8.5 mut/Mb

    Raccomandazioni: osimertinib
""")

# Access parsed data
print(f"Patient: {report.patient.id}")
print(f"Diagnosis: {report.diagnosis.primary_diagnosis}")
print(f"Variants: {len(report.variants)}")
print(f"TMB: {report.tmb} mut/Mb")
```

### Export to FHIR R4

```python
from mappers.fhir_mapper import FHIRMapper

fhir_mapper = FHIRMapper()
fhir_bundle = fhir_mapper.create_fhir_bundle(report)

# fhir_bundle contains:
# - Patient resource
# - Condition resource (diagnosis)
# - Observation resources (variants + TMB)
# - MedicationStatement resources
# - DiagnosticReport resource
```

### Export to GA4GH Phenopackets v2

```python
from mappers.phenopackets_mapper import PhenopacketsMapper

pheno_mapper = PhenopacketsMapper()
phenopacket = pheno_mapper.create_phenopacket(report)

# Phenopacket contains genomic interpretations
# following GA4GH standards
```

### Export to OMOP CDM

```python
from mappers.omop_mapper import OMOPMapper

omop_mapper = OMOPMapper()
omop_tables = omop_mapper.create_omop_tables(report)

# omop_tables contains:
# - person, condition_occurrence, measurement,
# - drug_exposure, specimen tables
```

### Quality Assessment

```python
from quality.quality_metrics import QualityAssessor

assessor = QualityAssessor()
quality_report = assessor.assess_report(report)

print(f"Quality Score: {quality_report.overall_score}/100")
print(f"Quality Level: {quality_report.quality_level}")
print(quality_report.get_summary())
```

### Export to Files

```python
from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter

# JSON export
json_exporter = JSONExporter(pretty=True)
package = json_exporter.export_complete_package(
    report=report,
    fhir_bundle=fhir_bundle,
    phenopacket=phenopacket,
    omop_tables=omop_tables
)
json_exporter.save_to_file(package, "output/report.json")

# CSV export
csv_exporter = CSVExporter()
csv_exporter.save_complete_export(report, "output/csv/")
```

---

## 📁 Project Structure

```
MTBParser/
├── vocabularies/              # Controlled vocabularies (JSON)
│   ├── icd_o_diagnoses.json   # ICD-O-3 oncology diagnoses
│   ├── rxnorm_drugs.json      # RxNorm targeted therapies
│   ├── hgnc_genes.json        # HGNC gene nomenclature
│   ├── snomed_ct_terms.json   # SNOMED-CT clinical terms
│   └── vocabulary_loader.py   # Dynamic vocabulary loading
│
├── core/                      # Core parsing engine
│   ├── data_models.py         # Dataclasses (Patient, Variant, etc.)
│   ├── pattern_extractors.py # NLP pattern extraction
│   └── mtb_parser.py          # Main parser
│
├── mappers/                   # Standard data mappers
│   ├── fhir_mapper.py         # FHIR R4 Bundle
│   ├── phenopackets_mapper.py # GA4GH Phenopackets v2
│   └── omop_mapper.py         # OMOP CDM v5.4
│
├── exporters/                 # Export modules
│   ├── json_exporter.py       # JSON export
│   └── csv_exporter.py        # CSV/TSV export
│
├── quality/                   # Quality assurance
│   └── quality_metrics.py     # Quality assessment & scoring
│
├── utils/                     # Utilities
│   ├── text_utils.py          # Text preprocessing
│   └── config.py              # Configuration
│
├── test_integration.py        # End-to-end integration test
└── requirements.txt           # Optional dependencies
```

---

## 🔬 Data Extraction

### Patient Information
- ID, age, sex, birth date
- Full demographic mapping

### Diagnosis
- Primary diagnosis with ICD-O-3 mapping
- Cancer stage (TNM/Roman numerals)
- Histology

### Genomic Variants
- **Gene**: HGNC-mapped gene symbols
- **HGVS nomenclature**: c.DNA and p.rotein changes
- **Classification**: Pathogenic, VUS, Benign (ACMG)
- **VAF**: Variant Allele Frequency (%)
- **Fusions**: Gene fusion detection (ALK::EML4, FGFR3::TACC3, etc.)

### Molecular Parameters
- **TMB**: Tumor Mutational Burden (mut/Mb)
- **NGS method**: Panel information

### Therapeutic Recommendations
- Drug names (RxNorm-mapped)
- Gene targets
- Evidence levels (FDA approved, clinical trial, etc.)

---

## 🧬 Supported Standards

### FHIR R4 (HL7 Fast Healthcare Interoperability Resources)
- **Patient**: Demographics
- **Condition**: Diagnosis (ICD-O)
- **Observation**: Genomic variants (LOINC codes)
- **MedicationStatement**: Therapeutic recommendations
- **DiagnosticReport**: Master genomic report

**LOINC Codes Used**:
- `69548-6`: Genetic variant assessment
- `48018-6`: Gene studied [ID]
- `48005-3`: Amino acid change (pHGVS)
- `48004-6`: DNA change (cHGVS)
- `81258-6`: Variant allele frequency
- `94076-7`: TMB Mutations/Mb
- `81247-9`: Master genetic panel

### GA4GH Phenopackets v2
- **Individual**: Patient with age and sex
- **Disease**: Diagnosis with ICD-O
- **GenomicInterpretation**: Variants with ACMG classification
- **VariationDescriptor**: VRS-based variant representation
- **MedicalAction**: Therapeutic recommendations
- **Measurement**: TMB and other molecular measurements

### OMOP CDM v5.4
- **PERSON**: Patient demographics
- **CONDITION_OCCURRENCE**: Diagnosis
- **MEASUREMENT**: Genomic variants, VAF, TMB
- **DRUG_EXPOSURE**: Therapeutic recommendations
- **SPECIMEN**: Tumor sample and NGS panel

---

## 📊 Quality Metrics

The system provides comprehensive quality assessment:

- **Overall Score**: 0-100 weighted score
- **Section Scores**: Patient, Diagnosis, Variants, Therapeutics
- **Quality Levels**: Excellent (90+), Good (75-89), Acceptable (60-74), Poor (40-59), Critical (<40)
- **Completeness**: Field filling percentage
- **Mapping Quality**: ICD-O, RxNorm, HGNC mapping rates
- **Warnings & Recommendations**: Actionable improvement suggestions

---

## 🧪 Testing

Run the complete integration test:

```bash
python3 test_integration.py
```

This tests:
- ✅ Vocabulary loading
- ✅ Text preprocessing
- ✅ MTB parsing
- ✅ Quality assessment
- ✅ All three mappers (FHIR, Phenopackets, OMOP)
- ✅ All exporters (JSON, CSV)
- ✅ Configuration validation

---

## 📝 Examples

See the complete example in `test_integration.py` which demonstrates:

1. Loading vocabularies
2. Parsing an Italian MTB report
3. Quality assessment
4. Mapping to FHIR, Phenopackets, and OMOP
5. Exporting to JSON and CSV

---

## 🔧 Configuration

Edit `utils/config.py` to customize:

- Vocabulary paths
- Quality thresholds
- TMB thresholds
- Export settings
- FHIR/Phenopackets/OMOP versions

---

## 📖 Documentation

- **CLAUDE.md**: AI-assisted development guide
- **FHIR IG**: https://hl7.org/fhir/genomics.html
- **Phenopackets**: https://phenopacket-schema.readthedocs.io/
- **OMOP CDM**: https://ohdsi.github.io/CommonDataModel/

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## 📄 License

[Add your license here]

---

## 👥 Authors

- **MTBParser Team**
- Generated with Claude Code assistance

---

## 🙏 Acknowledgments

- **Vocabularies**: ICD-O (WHO), RxNorm (NLM), HGNC, SNOMED-CT, LOINC
- **Standards**: HL7 FHIR, GA4GH, OHDSI OMOP
- **Guidelines**: AIOM, NCCN, AMP-ASCO-CAP

---

## 📧 Support

For issues and questions:
- GitHub Issues: [Repository URL]
- Email: [Contact email]

---

**MTBParser v1.0.0** - Making molecular oncology data interoperable 🧬
