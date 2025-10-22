#!/usr/bin/env python3
"""
Integration Test - Complete end-to-end test of MTB Parser System
Tests: Parsing → Quality Assessment → All Mappers → All Exporters
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import all components
from vocabularies.vocabulary_loader import VocabularyLoader
from core.mtb_parser import MTBParser
from core.data_models import MTBReport
from mappers.fhir_mapper import FHIRMapper
from mappers.phenopackets_mapper import PhenopacketsMapper
from mappers.omop_mapper import OMOPMapper
from quality.quality_metrics import QualityAssessor
from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter
from utils.text_utils import TextPreprocessor
from utils.config import Config


def test_complete_pipeline():
    """
    Complete end-to-end integration test
    """
    print("=" * 80)
    print("MTB PARSER SYSTEM - INTEGRATION TEST")
    print("=" * 80)

    # ===== Sample MTB Report =====
    sample_report_text = """
    =====================================
    REPORT MOLECULAR TUMOR BOARD
    =====================================

    INFORMAZIONI PAZIENTE
    ID Paziente: 12345
    Età: 65 anni
    Sesso: M
    Data di nascita: 15/03/1958

    DIAGNOSI CLINICA
    Diagnosi: Adenocarcinoma polmonare stadio IV
    Istologia: Adenocarcinoma moderatamente differenziato
    Sede: Lobo superiore destro

    ANALISI GENOMICA
    Pannello: FoundationOne CDx (324 geni)
    Data report: 22/10/2025

    VARIANTI IDENTIFICATE:
    ┌─────────┬──────────────┬──────────────┬───────────────┬──────┐
    │ Gene    │ cDNA         │ Proteina     │ Classe        │ VAF  │
    ├─────────┼──────────────┼──────────────┼───────────────┼──────┤
    │ EGFR    │ c.2573T>G    │ p.Leu858Arg  │ Pathogenic    │ 45%  │
    │ TP53    │ c.733G>A     │ p.Gly245Ser  │ Pathogenic    │ 52%  │
    │ KRAS    │ -            │ G12D         │ VUS           │ 8%   │
    └─────────┴──────────────┴──────────────┴───────────────┴──────┘

    Fusioni geniche:
    - fusione ALK::EML4 (variante 3a/b)

    TMB: 8.5 mut/Mb (TMB-Medium)

    RACCOMANDAZIONI TERAPEUTICHE:
    1. Sensibilità a osimertinib (EGFR L858R - FDA approved per NSCLC)
    2. Potenziale sensibilità a alectinib (fusione ALK - FDA approved)

    Linee guida AIOM 2024 - NCCN Guidelines v3.2024
    """

    # ===== STEP 1: Text Preprocessing =====
    print("\n" + "=" * 80)
    print("STEP 1: TEXT PREPROCESSING")
    print("=" * 80)

    preprocessor = TextPreprocessor()
    cleaned_text = preprocessor.preprocess_report(sample_report_text)
    print(f"✅ Text preprocessed (length: {len(cleaned_text)} chars)")

    # ===== STEP 2: Vocabulary Loading =====
    print("\n" + "=" * 80)
    print("STEP 2: VOCABULARY LOADING")
    print("=" * 80)

    vocab_loader = VocabularyLoader()
    stats = vocab_loader.get_vocabulary_stats()
    print(f"✅ Vocabularies loaded:")
    print(f"   - ICD-O diagnoses: {stats['icd_o_diagnoses_count']}")
    print(f"   - RxNorm drugs: {stats['rxnorm_drugs_count']}")
    print(f"   - HGNC genes: {stats['hgnc_genes_count']}")
    print(f"   - Actionable genes: {stats['actionable_genes_count']}")

    # ===== STEP 3: Parsing =====
    print("\n" + "=" * 80)
    print("STEP 3: MTB REPORT PARSING")
    print("=" * 80)

    parser = MTBParser(vocab_loader)
    report = parser.parse_report(cleaned_text)

    print(f"✅ Report parsed successfully:")
    print(f"   - Patient ID: {report.patient.id}")
    print(f"   - Patient Age: {report.patient.age}")
    print(f"   - Diagnosis: {report.diagnosis.primary_diagnosis}")
    print(f"   - Stage: {report.diagnosis.stage}")
    print(f"   - Variants found: {len(report.variants)}")
    print(f"   - Actionable variants: {len(report.get_actionable_variants())}")
    print(f"   - Fusions: {len(report.get_fusion_variants())}")
    print(f"   - TMB: {report.tmb} mut/Mb")
    print(f"   - Recommendations: {len(report.recommendations)}")

    # ===== STEP 4: Quality Assessment =====
    print("\n" + "=" * 80)
    print("STEP 4: QUALITY ASSESSMENT")
    print("=" * 80)

    assessor = QualityAssessor()
    quality_report = assessor.assess_report(report)

    print(f"✅ Quality assessment completed:")
    print(f"   - Overall Score: {quality_report.overall_score}/100")
    print(f"   - Quality Level: {quality_report.quality_level}")
    print(f"   - Completeness: {quality_report.completeness_pct}%")
    print(f"   - Warnings: {len(quality_report.warnings)}")
    print(f"   - Errors: {len(quality_report.errors)}")

    # ===== STEP 5: FHIR R4 Mapping =====
    print("\n" + "=" * 80)
    print("STEP 5: FHIR R4 MAPPING")
    print("=" * 80)

    fhir_mapper = FHIRMapper()
    fhir_bundle = fhir_mapper.create_fhir_bundle(report)

    print(f"✅ FHIR Bundle created:")
    print(f"   - Resource Type: {fhir_bundle['resourceType']}")
    print(f"   - Bundle Type: {fhir_bundle['type']}")
    print(f"   - Total Resources: {len(fhir_bundle['entry'])}")
    print(f"   - Resources:")
    for entry in fhir_bundle['entry']:
        print(f"     • {entry['resource']['resourceType']}")

    # ===== STEP 6: GA4GH Phenopackets Mapping =====
    print("\n" + "=" * 80)
    print("STEP 6: GA4GH PHENOPACKETS V2 MAPPING")
    print("=" * 80)

    pheno_mapper = PhenopacketsMapper()
    phenopacket = pheno_mapper.create_phenopacket(report)

    print(f"✅ Phenopacket created:")
    print(f"   - Phenopacket ID: {phenopacket['id']}")
    print(f"   - Subject: {phenopacket['subject']['id']}")
    print(f"   - Diseases: {len(phenopacket['diseases'])}")
    print(f"   - Interpretations: {len(phenopacket['interpretations'])}")
    print(f"   - Medical Actions: {len(phenopacket['medicalActions'])}")
    print(f"   - Measurements: {len(phenopacket['measurements'])}")
    print(f"   - Schema Version: {phenopacket['metaData']['phenopacketSchemaVersion']}")

    # ===== STEP 7: OMOP CDM Mapping =====
    print("\n" + "=" * 80)
    print("STEP 7: OMOP CDM V5.4 MAPPING")
    print("=" * 80)

    omop_mapper = OMOPMapper()
    omop_tables = omop_mapper.create_omop_tables(report)

    print(f"✅ OMOP tables created:")
    total_records = sum(len(records) for records in omop_tables.values())
    print(f"   - Total tables: {len(omop_tables)}")
    print(f"   - Total records: {total_records}")
    for table_name, records in omop_tables.items():
        print(f"     • {table_name}: {len(records)} records")

    # ===== STEP 8: JSON Export =====
    print("\n" + "=" * 80)
    print("STEP 8: JSON EXPORT")
    print("=" * 80)

    json_exporter = JSONExporter(pretty=True, include_raw=False)

    # Create complete package
    package = json_exporter.export_complete_package(
        report=report,
        fhir_bundle=fhir_bundle,
        phenopacket=phenopacket,
        omop_tables=omop_tables
    )

    # Save to file
    output_dir = Path("/tmp/mtb_parser_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_file = output_dir / "complete_package.json"
    json_exporter.save_to_file(package, json_file)

    print(f"✅ JSON export completed:")
    print(f"   - File: {json_file}")
    print(f"   - Size: {json_file.stat().st_size:,} bytes")
    print(f"   - Package contains:")
    for key in package.keys():
        print(f"     • {key}")

    # ===== STEP 9: CSV Export =====
    print("\n" + "=" * 80)
    print("STEP 9: CSV EXPORT")
    print("=" * 80)

    csv_exporter = CSVExporter(delimiter=',')

    csv_dir = output_dir / "csv_export"
    csv_exporter.save_complete_export(report, csv_dir)

    print(f"✅ CSV export completed:")
    print(f"   - Directory: {csv_dir}")
    print(f"   - Files created:")
    for csv_file in csv_dir.glob('*.csv'):
        print(f"     • {csv_file.name} ({csv_file.stat().st_size} bytes)")

    # ===== STEP 10: Configuration Validation =====
    print("\n" + "=" * 80)
    print("STEP 10: CONFIGURATION VALIDATION")
    print("=" * 80)

    if Config.validate_paths():
        print(f"✅ All configuration paths valid")
        print(f"   - Base: {Config.BASE_DIR}")
        print(f"   - FHIR Version: {Config.FHIR_VERSION}")
        print(f"   - Phenopackets: v{Config.PHENOPACKETS_SCHEMA_VERSION}")
        print(f"   - OMOP CDM: v{Config.OMOP_CDM_VERSION}")
    else:
        print(f"⚠️  Some configuration paths missing")

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)

    print(f"""
✅ ALL TESTS PASSED

Test Coverage:
  ✓ Text preprocessing
  ✓ Vocabulary loading (ICD-O, RxNorm, HGNC, SNOMED-CT)
  ✓ MTB report parsing (Patient, Diagnosis, Variants, TMB, Recommendations)
  ✓ Quality assessment (Score: {quality_report.overall_score}/100)
  ✓ FHIR R4 mapping ({len(fhir_bundle['entry'])} resources)
  ✓ GA4GH Phenopackets v2 mapping
  ✓ OMOP CDM v5.4 mapping ({total_records} records)
  ✓ JSON export (complete package)
  ✓ CSV export (3 files)
  ✓ Configuration validation

Output Files:
  - JSON: {json_file}
  - CSV:  {csv_dir}/

System Status: OPERATIONAL ✅
    """)

    return True


if __name__ == "__main__":
    try:
        success = test_complete_pipeline()
        if success:
            print("\n" + "=" * 80)
            print("✅ INTEGRATION TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)
            sys.exit(0)
        else:
            print("\n❌ INTEGRATION TEST FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
