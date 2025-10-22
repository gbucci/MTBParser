# MTBParser - Complete File Index

## 📚 Documentation

- **README_NEW.md** - Complete user guide with examples
- **PROJECT_SUMMARY.md** - Implementation summary and metrics
- **CLAUDE.md** - AI-assisted development guide
- **requirements.txt** - Python dependencies (optional)
- **INDEX.md** - This file

---

## 🗂️ Vocabularies (vocabularies/)

### JSON Vocabularies
- **icd_o_diagnoses.json** (15 diagnoses)
  - ICD-O-3 oncology diagnoses with topography codes
  - Metadata: version 3.2, WHO ICD-O-3

- **rxnorm_drugs.json** (26 drugs)
  - Targeted oncology therapies with RxNorm codes
  - Drug-gene targets, indications, evidence levels
  - Metadata: AIOM, NCCN, AMP-ASCO-CAP guidelines

- **hgnc_genes.json** (37 genes)
  - Cancer-relevant genes with HGNC codes
  - Chromosome locations, cancer types, actionability
  - 22 actionable genes identified

- **snomed_ct_terms.json**
  - Clinical findings, procedures, specimens
  - Variant classification mappings (Italian → ACMG)

### Python Modules
- **vocabulary_loader.py**
  - Dynamic vocabulary loading with fuzzy matching
  - Diagnosis, drug, and gene mapping
  - Vocabulary statistics and validation

---

## 🔧 Core Engine (core/)

- **data_models.py**
  - `Variant`: Genomic variants (gene, HGVS, classification, VAF)
  - `Patient`: Demographics
  - `Diagnosis`: Primary diagnosis, stage, histology
  - `TherapeuticRecommendation`: Drugs with evidence
  - `QualityMetrics`: Parsing quality metrics
  - `MTBReport`: Complete report structure

- **pattern_extractors.py**
  - NLP pattern library for entity extraction
  - Patient info extraction
  - Diagnosis extraction with ICD-O mapping
  - Variant extraction (tabular, inline, fusions)
  - TMB extraction
  - Therapeutic recommendation extraction

- **mtb_parser.py**
  - Main parser orchestrator
  - Combines pattern extraction with vocabulary mapping
  - Quality metrics calculation
  - NGS method and report date extraction

---

## 🔄 Mappers (mappers/)

- **fhir_mapper.py** - FHIR R4 Mapper
  - Creates FHIR Bundle (transaction type)
  - Resources: Patient, Condition, Observation (variants + TMB), MedicationStatement, DiagnosticReport
  - LOINC codes: 69548-6, 48018-6, 48005-3, 48004-6, 81258-6, 94076-7, 81247-9
  - Following FHIR Genomics Reporting IG

- **phenopackets_mapper.py** - GA4GH Phenopackets v2 Mapper
  - Creates Phenopacket v2.0 JSON
  - Components: Individual, Disease, GenomicInterpretation, VariationDescriptor, Measurement, MedicalAction
  - VRS-based variant representation
  - HGVS expression support

- **omop_mapper.py** - OMOP CDM v5.4 Mapper
  - Creates 6 OMOP tables
  - Tables: PERSON, CONDITION_OCCURRENCE, MEASUREMENT, DRUG_EXPOSURE, SPECIMEN, OBSERVATION
  - OMOP concept ID mapping
  - Optimized for observational research

---

## 📤 Exporters (exporters/)

- **json_exporter.py**
  - Export individual formats (MTB, FHIR, Phenopackets, OMOP)
  - Complete package export (all formats combined)
  - Pretty printing and raw content options
  - Save to file functionality

- **csv_exporter.py**
  - Export variants to CSV
  - Export recommendations to CSV
  - Export patient summary to CSV
  - Customizable delimiter and encoding
  - Complete export (all 3 CSVs)

---

## 📊 Quality (quality/)

- **quality_metrics.py**
  - `DetailedQualityReport`: Comprehensive quality report
  - `QualityAssessor`: Quality assessment engine
  - Overall score (0-100) and quality level classification
  - Section scores: Patient, Diagnosis, Variants, Therapeutics
  - Completeness and mapping quality metrics
  - Automated warnings and recommendations

---

## 🛠️ Utilities (utils/)

- **text_utils.py**
  - `TextPreprocessor`: Text cleaning utilities
  - Whitespace normalization
  - Italian character normalization
  - Section extraction
  - Gene/drug name cleaning
  - Full preprocessing pipeline

- **config.py**
  - `Config`: System configuration
  - Directory paths
  - Quality thresholds (completeness, mapping, TMB)
  - Export settings
  - Standard versions (FHIR R4, Phenopackets v2, OMOP v5.4)
  - Path validation

---

## 🧪 Testing

- **test_integration.py**
  - Complete end-to-end integration test
  - Tests all 10 system components
  - Validates: vocabularies, parsing, quality, mappers, exporters
  - Creates sample outputs in `/tmp/mtb_parser_test/`
  - Test status: ✅ PASSING

---

## 📦 Legacy/Reference

- **mtb_parser.py** (root level)
  - Original monolithic parser
  - Kept for reference
  - Functionality now split across core/, mappers/, quality/

- **Structure.txt** - Original structure plan
- **project_structure.txt** - Detailed structure specification

---

## 📋 File Count Summary

| Category | Files | Total Lines* |
|----------|-------|--------------|
| Vocabularies (JSON) | 4 | ~400 |
| Vocabularies (Python) | 1 | ~250 |
| Core | 3 | ~1,200 |
| Mappers | 3 | ~1,800 |
| Exporters | 2 | ~400 |
| Quality | 1 | ~400 |
| Utils | 2 | ~250 |
| Testing | 1 | ~350 |
| Documentation | 5 | ~1,200 |
| **TOTAL** | **22** | **~6,250** |

*Approximate line counts including code, comments, and documentation

---

## 🔍 Quick Reference

### Most Important Files

**For End Users:**
1. `README_NEW.md` - Start here
2. `test_integration.py` - See it in action
3. `core/mtb_parser.py` - Main entry point

**For Developers:**
1. `CLAUDE.md` - Development guide
2. `core/data_models.py` - Data structures
3. `core/pattern_extractors.py` - Extraction logic
4. `PROJECT_SUMMARY.md` - Implementation details

**For Integration:**
1. `mappers/fhir_mapper.py` - FHIR integration
2. `mappers/phenopackets_mapper.py` - GA4GH integration
3. `mappers/omop_mapper.py` - OMOP integration

---

## 🚀 Quick Start Path

```
1. Read: README_NEW.md
2. Run:  python3 test_integration.py
3. Use:  core/mtb_parser.py → mappers → exporters
4. Extend: vocabularies → pattern_extractors
```

---

**Last Updated**: October 22, 2025
**Version**: 1.0.0
**Status**: ✅ Complete & Operational
